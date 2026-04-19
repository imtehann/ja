from voice import Voice
from wakeword import WakeWord
from brain import ask_jarvis, load_memory, save_memory
from actions import play_youtube, scroll_for_minutes, open_website, open_folder, take_screenshot
import time
import threading

def run_gesture_monitor():
    # Optional: run in background
    pass

def main():
    voice = Voice()
    wake = WakeWord()
    memory = load_memory()
    
    voice.speak("Jarvis ready. Say 'Hey Jarvis' to wake me.")
    
    # Main loop
    while True:
        # Wait for wake word
        if wake.use_porcupine:
            print("Waiting for 'Jarvis'...")
            while not wake.listen():
                time.sleep(0.1)
        else:
            # Fallback: ask user to say "hey jarvis" via voice
            wake_phrase = voice.listen(timeout=3)
            if not wake_phrase or "hey jarvis" not in wake_phrase:
                continue
        
        # Activated
        voice.speak("Yes sir? What is your problem?")
        user_input = voice.listen(timeout=8)
        if not user_input:
            voice.speak("I didn't hear anything.")
            continue
        
        # Check for direct actions first
        if "play" in user_input and "youtube" in user_input or ("play" in user_input and "song" in user_input):
            query = user_input.replace("play", "").replace("youtube", "").replace("song", "").strip()
            play_youtube(query)
            voice.speak(f"Playing {query} on YouTube")
        elif "scroll" in user_input:
            scroll_for_minutes(10)
            voice.speak("Scrolling completed.")
        elif "open website" in user_input:
            site = user_input.replace("open website", "").strip()
            open_website(site)
            voice.speak(f"Opening {site}")
        elif "open folder" in user_input:
            path = user_input.replace("open folder", "").strip()
            open_folder(path)
            voice.speak("Folder opened")
        elif "screenshot" in user_input:
            file = take_screenshot()
            voice.speak(f"Screenshot saved as {file}")
        else:
            # Use AI brain with memory
            context = "\n".join([f"User: {c['user']}\nJarvis: {c['jarvis']}" for c in memory[-3:]])
            answer = ask_jarvis(user_input, context)
            voice.speak(answer)
            memory.append({"user": user_input, "jarvis": answer})
            save_memory(memory)
        
        # Proactive follow-up
        voice.speak("Anything else, sir?")
        more = voice.listen(timeout=5)
        if more and "no" in more.lower():
            voice.speak("Say 'Hey Jarvis' to wake me again.")
        elif more:
            # Continue loop without re-waking
            user_input = more
            # repeat action handling...
    
if __name__ == "__main__":
    main()