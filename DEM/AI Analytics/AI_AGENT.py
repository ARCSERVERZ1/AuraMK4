import os
import time
import pyautogui
import pyperclip


shortcut_path = r"C:\Users\bs\Desktop\ChatGPT Sanjay.lnk"


def find_image(image_path, confidence=0.8, timeout=5):
    """
    Search image on screen for X seconds.
    Returns location if found, else None.
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            location = pyautogui.locateCenterOnScreen(
                image_path,
                confidence=confidence
            )

            if location:
                return location

        except Exception:
            pass

        time.sleep(0.2)

    return None


# -------------------------
# Open shortcut
# -------------------------
if os.path.exists(shortcut_path):
    os.startfile(shortcut_path)
    print("Opened ChatGPT shortcut")
else:
    print("Shortcut not found:", shortcut_path)
    exit()

# Wait for app/browser to load
time.sleep(5)

# -------------------------
# Find search/input bar
# -------------------------
location = find_image(
    "SearchBar.png",
    confidence=0.7,
    timeout=10
)

if location:
    print("Found at:", location)

    # Click input box
    pyautogui.click(location)




    # Paste (Ctrl + V)
    pyautogui.hotkey("ctrl", "v")

    time.sleep(0.5)

    # Press Enter
    pyautogui.press("enter")

    print("Message pasted and Enter pressed")

else:
    print("Search bar not found")