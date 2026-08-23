import requests
import json
import pyperclip
import os
import time
import threading
import tkinter as tk
from tkinter import ttk
import pyautogui


# ==========================================================
# CONFIG
# ==========================================================

API_GET_UNCLASSIFIED_DATA = (
    "http://127.0.0.1:8000/dem/api/ai_analytics"
)

API_BULK_UPDATE = (
    "http://127.0.0.1:8000/dem/api/bulk-update-transactions/"
)

SHORTCUT_PATH = r"C:\Users\bs\Desktop\ChatGPT Sanjay.lnk"

SEARCH_BAR_IMAGE = "SearchBar.png"
COPY_IMAGE = "Copy.png"

WAIT_AFTER_SEND_SECONDS = 70


# ==========================================================
# INPUTS (CHANGE THESE)
# ==========================================================

USER_NAME = "Sanjay"

START_DATE = "2026-05-01"
END_DATE = "2026-05-23"

PROMPT_TEMPLATE_FILE = (
    "PROMPT_TEMPLATE_AI_CLASSIFICATION.txt"
)


# ==========================================================
# TKINTER STATUS WINDOW
# ==========================================================

root = tk.Tk()
root.title("Aura AI Automation")
root.geometry("550x220")
root.resizable(False, False)
root.attributes("-topmost", True)

status_var = tk.StringVar(
    value="Waiting to start..."
)

timer_var = tk.StringVar(
    value=""
)

title_label = tk.Label(
    root,
    text="AI Classification Automation",
    font=("Segoe UI", 14, "bold")
)
title_label.pack(pady=10)

status_label = tk.Label(
    root,
    textvariable=status_var,
    font=("Segoe UI", 11),
    wraplength=520,
    justify="center"
)
status_label.pack()

timer_label = tk.Label(
    root,
    textvariable=timer_var,
    font=("Segoe UI", 10)
)
timer_label.pack(pady=5)

progress = ttk.Progressbar(
    root,
    orient="horizontal",
    length=450,
    mode="indeterminate"
)
progress.pack(pady=10)


# ==========================================================
# STATUS HELPERS
# ==========================================================

def set_status(message):
    print(message)
    root.after(
        0,
        lambda: status_var.set(message)
    )


def set_timer(message):
    root.after(
        0,
        lambda: timer_var.set(message)
    )


# ==========================================================
# PROMPT BUILDER
# ==========================================================

def build_prompt_from_txt(
        txt_file_path: str,
        api_data: dict
):
    set_status(
        "Reading prompt template..."
    )

    with open(
            txt_file_path,
            "r",
            encoding="utf-8"
    ) as file:
        prompt_template = file.read()

    category_json = json.dumps(
        api_data.get("category", []),
        ensure_ascii=False,
        indent=2
    )

    transactions_json = json.dumps(
        api_data.get("Txns", []),
        ensure_ascii=False,
        indent=2
    )

    final_prompt = prompt_template.format(
        category=category_json,
        transactions=transactions_json
    )

    pyperclip.copy(final_prompt)

    set_status(
        "Prompt copied to clipboard ✅"
    )

    return final_prompt


# ==========================================================
# IMAGE FINDER
# ==========================================================

def find_image(
        image_path,
        confidence=0.8,
        timeout=10
):
    start_time = time.time()

    while (
            time.time() - start_time
            < timeout
    ):
        try:
            location = (
                pyautogui
                .locateCenterOnScreen(
                    image_path,
                    confidence=confidence
                )
            )

            if location:
                return location

        except Exception:
            pass

        time.sleep(0.2)

    return None


# ==========================================================
# WAIT TIMER
# ==========================================================

def countdown(seconds):
    for remaining in range(
            seconds,
            0,
            -1
    ):
        mins = remaining // 60
        secs = remaining % 60

        set_timer(
            f"Waiting: "
            f"{mins:02d}:{secs:02d}"
        )

        time.sleep(1)

    set_timer("")


# ==========================================================
# BULK UPDATE
# ==========================================================

def bulk_update_from_clipboard():
    try:
        set_status(
            "Reading copied response..."
        )

        text = (
            pyperclip
            .paste()
            .strip()
        )

        if not text:
            set_status(
                "Clipboard empty ❌"
            )
            return

        # remove markdown fences
        text = text.replace(
            "```json",
            ""
        )

        text = text.replace(
            "```",
            ""
        ).strip()

        set_status(
            "Parsing JSON..."
        )

        data = json.loads(text)

        transactions = data.get(
            "classified_transactions"
        )

        if not transactions:
            set_status(
                "No classified_transactions ❌"
            )
            return

        set_status(
            f"Sending "
            f"{len(transactions)} "
            f"transactions..."
        )

        response = requests.post(
            API_BULK_UPDATE,
            json=transactions,
            timeout=60
        )

        response.raise_for_status()

        try:
            result = response.json()
        except Exception:
            result = response.text

        set_status(
            f"Bulk update success ✅ "
            f"{result}"
        )

    except json.JSONDecodeError as e:
        set_status(
            f"Invalid JSON ❌ {e}"
        )

    except Exception as e:
        set_status(
            f"Bulk update failed ❌ {e}"
        )


# ==========================================================
# MAIN AUTOMATION
# ==========================================================

def run_automation():
    try:
        progress.start()

        # ------------------------------------------
        # FETCH DATA
        # ------------------------------------------
        set_status(
            "Fetching transactions..."
        )

        payload = {
            "user": USER_NAME,
            "start_date": START_DATE,
            "end_date": END_DATE
        }

        response = requests.post(
            API_GET_UNCLASSIFIED_DATA,
            data=payload,
            timeout=30
        )

        response.raise_for_status()

        api_data = response.json()

        set_status(
            "API response received ✅"
        )

        # ------------------------------------------
        # BUILD PROMPT
        # ------------------------------------------
        build_prompt_from_txt(
            PROMPT_TEMPLATE_FILE,
            api_data
        )

        # ------------------------------------------
        # OPEN CHATGPT
        # ------------------------------------------
        set_status(
            "Opening ChatGPT..."
        )

        if os.path.exists(
                SHORTCUT_PATH
        ):
            os.startfile(
                SHORTCUT_PATH
            )
        else:
            set_status(
                "Shortcut not found ❌"
            )
            return

        set_status(
            "Waiting for ChatGPT..."
        )

        time.sleep(5)

        # ------------------------------------------
        # FIND SEARCH BAR
        # ------------------------------------------
        set_status(
            "Searching input box..."
        )

        location = find_image(
            SEARCH_BAR_IMAGE,
            confidence=0.7,
            timeout=20
        )

        if not location:
            set_status(
                "Search bar not found ❌"
            )
            return

        set_status(
            "Search bar found ✅"
        )

        pyautogui.click(location)

        time.sleep(1)

        # ------------------------------------------
        # PASTE + SEND
        # ------------------------------------------
        set_status(
            "Pasting prompt..."
        )

        pyautogui.hotkey(
            "ctrl",
            "v"
        )

        time.sleep(1)

        set_status(
            "Sending prompt..."
        )

        pyautogui.press("enter")

        set_status(
            "Prompt submitted ✅"
        )

        # ------------------------------------------
        # WAIT FOR RESPONSE
        # ------------------------------------------
        countdown(
            WAIT_AFTER_SEND_SECONDS
        )

        # ------------------------------------------
        # SCROLL DOWN
        # ------------------------------------------
        set_status(
            "Scrolling..."
        )

        pyautogui.scroll(-1000)
        time.sleep(1)

        pyautogui.scroll(-1000)
        time.sleep(2)

        # ------------------------------------------
        # FIND COPY BUTTON
        # ------------------------------------------
        set_status(
            "Searching copy button..."
        )

        copy_location = find_image(
            COPY_IMAGE,
            confidence=0.7,
            timeout=25
        )

        if not copy_location:
            set_status(
                "Copy button not found ❌"
            )
            return

        pyautogui.click(
            copy_location
        )

        set_status(
            "Copied response ✅"
        )

        time.sleep(2)

        # ------------------------------------------
        # BULK UPDATE
        # ------------------------------------------
        bulk_update_from_clipboard()

        set_status(
            "Automation complete 🎉"
        )

    except Exception as e:
        set_status(
            f"Error ❌ {e}"
        )

    finally:
        progress.stop()


# ==========================================================
# START
# ==========================================================

threading.Thread(
    target=run_automation,
    daemon=True
).start()

root.mainloop()