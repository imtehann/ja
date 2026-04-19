"""
Jarvis - Personal AI Assistant (Python Backend)
Requires: pip install anthropic requests beautifulsoup4 yfinance
"""

import os
import json
import re
import anthropic
import yfinance as yf
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# ── Config ─────────────────────────────────────────────────────────────────
MEMORY_FILE = "jarvis_memory.json"
HISTORY_FILE = "jarvis_history.json"
API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")   # or paste key directly

client = anthropic.Anthropic(api_key=API_KEY)
MODEL = "claude-sonnet-4-20250514"

# ── Memory ──────────────────────────────────────────────────────────────────
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE) as f:
            return json.load(f)
    return []

def save_memory(mem):
    with open(MEMORY_FILE, "w") as f:
        json.dump(mem, f, indent=2)

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE) as f:
            return json.load(f)
    return []

def save_history(hist):
    with open(HISTORY_FILE, "w") as f:
        json.dump(hist[-40:], f, indent=2)  # keep last 40 messages

# ── Stock module ─────────────────────────────────────────────────────────────
def get_stock_info(symbol: str) -> str:
    try:
        ticker = yf.Ticker(symbol.upper())
        info = ticker.info
        hist = ticker.history(period="5d")

        name = info.get("longName", symbol)
        price = info.get("currentPrice") or info.get("regularMarketPrice", "N/A")
        prev_close = info.get("previousClose", "N/A")
        change = ((price - prev_close) / prev_close * 100) if isinstance(price, float) and isinstance(prev_close, float) else "N/A"
        market_cap = info.get("marketCap", "N/A")
        pe = info.get("trailingPE", "N/A")
        week_high = info.get("fiftyTwoWeekHigh", "N/A")
        week_low = info.get("fiftyTwoWeekLow", "N/A")
        analyst = info.get("recommendationKey", "N/A")
        summary = info.get("longBusinessSummary", "")[:300]

        change_str = f"{change:+.2f}%" if isinstance(change, float) else "N/A"

        return (
            f"Symbol: {symbol.upper()} — {name}\n"
            f"Price: ${price}  |  Change: {change_str}\n"
            f"52-week range: ${week_low} – ${week_high}\n"
            f"Market cap: {market_cap:,}" if isinstance(market_cap, int) else f"Market cap: {market_cap}" + "\n"
            f"P/E ratio: {pe}  |  Analyst rating: {analyst}\n"
            f"About: {summary}..."
        )
    except Exception as e:
        return f"Could not fetch stock data for '{symbol}': {e}"

# ── Web search module (DuckDuckGo HTML scrape) ────────────────────────────────
def web_search(query: str, max_results: int = 5) -> str:
    try:
        url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"
        headers = {"User-Agent": "Mozilla/5.0 (compatible; JarvisBot/1.0)"}
        resp = requests.get(url, headers=headers, timeout=8)
        soup = BeautifulSoup(resp.text, "html.parser")
        results = []
        for r in soup.select(".result__body")[:max_results]:
            title = r.select_one(".result__title")
            snippet = r.select_one(".result__snippet")
            link = r.select_one(".result__url")
            if title and snippet:
                results.append(
                    f"• {title.get_text(strip=True)}\n"
                    f"  {snippet.get_text(strip=True)}\n"
                    f"  {link.get_text(strip=True) if link else ''}"
                )
        return "\n\n".join(results) if results else "No results found."
    except Exception as e:
        return f"Search failed: {e}"

# ── Book module ──────────────────────────────────────────────────────────────
def summarize_book(title: str, memory: list, history: list) -> str:
    prompt = (
        f"Please provide a comprehensive summary of the book '{title}'. "
        "Include: 1) Overview and author background, 2) Key themes, "
        "3) Chapter-by-chapter highlights, 4) Key quotes, 5) Main takeaways."
    )
    return chat_with_jarvis(prompt, memory, history, mode="book")

# ── Core chat ────────────────────────────────────────────────────────────────
SYSTEM_PROMPTS = {
    "chat": (
        "You are Jarvis, a loyal, helpful AI assistant. Be concise but thorough. "
        "End responses with 'Is there anything else I can do for you, sir?' when appropriate."
    ),
    "search": (
        "You are Jarvis. You have been given web search results. "
        "Synthesize them into a clear, well-organized answer. Cite sources."
    ),
    "stock": (
        "You are Jarvis providing stock analysis. Given the stock data, provide: "
        "technical outlook (bullish/bearish/neutral), key risks, short-term prediction. "
        "Always end with 'Prediction, not financial advice.'"
    ),
    "book": (
        "You are Jarvis. Provide a thorough, well-structured book summary with key themes, "
        "chapter highlights, key quotes, and main takeaways."
    ),
}

def chat_with_jarvis(user_input: str, memory: list, history: list, mode: str = "chat") -> str:
    mem_str = "\n".join(f"- {m}" for m in memory) if memory else "None"
    system = SYSTEM_PROMPTS.get(mode, SYSTEM_PROMPTS["chat"])
    system += f"\n\nUser memory:\n{mem_str}"

    history.append({"role": "user", "content": user_input})
    if len(history) > 20:
        history = history[-20:]

    response = client.messages.create(
        model=MODEL,
        max_tokens=1000,
        system=system,
        messages=history,
    )
    reply = response.content[0].text
    history.append({"role": "assistant", "content": reply})
    return reply

# ── Command router ────────────────────────────────────────────────────────────
def handle_command(user_input: str, memory: list, history: list) -> str:
    lower = user_input.strip().lower()

    # Memory commands
    if lower.startswith("remember:") or lower.startswith("save:"):
        item = re.sub(r"^(remember:|save:)\s*", "", user_input, flags=re.I).strip()
        memory.append(item)
        save_memory(memory)
        return f"Saved to memory: \"{item}\"\nTotal memories: {len(memory)}. Is there anything else, sir?"

    if lower in ("show memory", "recall all", "list memory"):
        if not memory:
            return "No memories saved yet, sir."
        return "Here is everything I remember, sir:\n" + "\n".join(f"{i+1}. {m}" for i, m in enumerate(memory))

    if lower.startswith("forget:"):
        item = re.sub(r"^forget:\s*", "", user_input, flags=re.I).strip()
        before = len(memory)
        memory[:] = [m for m in memory if item.lower() not in m.lower()]
        save_memory(memory)
        removed = before - len(memory)
        return f"Removed {removed} item(s) matching '{item}'. Is there anything else, sir?"

    # Stock command: [STOCK: AAPL] or "stock AAPL"
    stock_match = re.match(r"(?:\[STOCK:\s*(\w+)\]|stock\s+(\w+))", lower)
    if stock_match:
        symbol = (stock_match.group(1) or stock_match.group(2)).upper()
        data = get_stock_info(symbol)
        return chat_with_jarvis(f"Here is the live data:\n{data}\nProvide analysis.", memory, history, mode="stock")

    # Search command: [SEARCH: query] or "search ..."
    search_match = re.match(r"(?:\[SEARCH:\s*(.+)\]|search\s+(.+))", lower)
    if search_match:
        query = (search_match.group(1) or search_match.group(2)).strip()
        results = web_search(query)
        return chat_with_jarvis(f"Search results for '{query}':\n\n{results}\n\nSynthesize these results.", memory, history, mode="search")

    # Book command: [BOOK: title] or "summarize book ..."
    book_match = re.match(r"(?:\[BOOK:\s*(.+)\]|summarize book\s+(.+)|book summary\s+(.+))", lower)
    if book_match:
        title = (book_match.group(1) or book_match.group(2) or book_match.group(3)).strip()
        return summarize_book(title, memory, history)

    # Default: general chat
    return chat_with_jarvis(user_input, memory, history)

# ── Main REPL ────────────────────────────────────────────────────────────────
def main():
    print("\n" + "="*55)
    print("  JARVIS — Personal AI Assistant (Python)")
    print("="*55)
    print("Commands:")
    print("  remember: <item>      — save to memory")
    print("  show memory           — list all memories")
    print("  forget: <item>        — remove from memory")
    print("  stock <SYMBOL>        — stock analysis")
    print("  search <query>        — web search")
    print("  book summary <title>  — summarize a book")
    print("  quit / exit           — exit")
    print("="*55 + "\n")

    if not API_KEY:
        print("WARNING: ANTHROPIC_API_KEY not set. Set it as an env variable or edit jarvis.py.\n")

    memory = load_memory()
    history = load_history()

    print(f"Jarvis: Hello, sir. I have {len(memory)} memories loaded. Ready.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nJarvis: Goodbye, sir.")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "bye"):
            print("Jarvis: Goodbye, sir.")
            break

        print("Jarvis: [thinking...]\r", end="", flush=True)
        reply = handle_command(user_input, memory, history)
        save_history(history)
        print(f"Jarvis: {reply}\n")

if __name__ == "__main__":
    main()
