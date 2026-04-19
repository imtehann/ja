import pyautogui
import webbrowser
import pywhatkit
import os
import time

def play_youtube(video):
    pywhatkit.playonyt(video)

def scroll_for_minutes(minutes=10):
    end_time = time.time() + minutes * 60
    while time.time() < end_time:
        pyautogui.scroll(-300)
        time.sleep(1)

def open_website(url):
    if not url.startswith("http"):
        url = "https://" + url
    webbrowser.open(url)

def open_folder(path):
    os.startfile(path)

def take_screenshot():
    pyautogui.screenshot("screenshot.png")
    return "screenshot.png"