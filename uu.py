import json
import requests
from bs4 import BeautifulSoup
import os
from config import OPENAI_API_KEY

MEMORY_FILE = "memory.json"

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return []

def save_memory(conv):
    with open(MEMORY_FILE, "w") as f:
        json.dump(conv[-50:], f, indent=2)

def search_web(query):
    """Free DuckDuckGo search fallback"""
    url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        results = soup.find_all("a", class_="result__a")
        snippets = soup.find_all("a", class_="result__snippet")
        if results:
            title = results[0].get_text()
            snippet = snippets[0].get_text() if snippets else ""
            return f"{title}. {snippet[:300]}"
        return "No results found."
    except:
        return "Search failed."

def ask_jarvis(user_input, memory_context=""):
    # If OpenAI key is available, use GPT
    if OPENAI_API_KEY:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_API_KEY)
            system = """You are Jarvis, a loyal AI assistant. You help with PC control, research, coding.
            Use the memory and web search below. Answer concisely."""
            web_result = search_web(user_input)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": f"Memory: {memory_context}\nWeb: {web_result}\nUser: {user_input}"}
                ],
                max_tokens=300
            )
            return response.choices[0].message.content
        except:
            pass
    # Fallback: just return web search
    return search_web(user_input)