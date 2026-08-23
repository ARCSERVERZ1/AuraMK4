import os
import shutil
from tkinter import Tk, Label
from PIL import Image, ImageTk

# ================= CONFIG =================
IMAGE_FOLDER = r"G:\wedf\Stills"       # Folder containing images
COPY_TO_FOLDER = r"G:\still_python_sort"   # Default folder (z key)
SUPPORTED_FORMATS = (".jpg", ".jpeg", ".png", ".bmp")
# =========================================

os.makedirs(COPY_TO_FOLDER, exist_ok=True)

images = [f for f in os.listdir(IMAGE_FOLDER) if f.lower().endswith(SUPPORTED_FORMATS)]
current_index = 0

root = Tk()
root.title("Image Viewer (Press Z to copy image)")
root.geometry("900x700")

label = Label(root)
label.pack(expand=True)

def show_image():
    global img_tk
    image_path = os.path.join(IMAGE_FOLDER, images[current_index])
    img = Image.open(image_path)
    img.thumbnail((850, 650))
    img_tk = ImageTk.PhotoImage(img)
    label.config(image=img_tk)
    root.title(f"{images[current_index]} ({current_index+1}/{len(images)})")

def copy_image():
    src = os.path.join(IMAGE_FOLDER, images[current_index])
    dst = os.path.join(COPY_TO_FOLDER, images[current_index])

    # avoid overwrite
    if not os.path.exists(dst):
        shutil.copy2(src, dst)
        print(f"Copied: {images[current_index]}")
    else:
        print(f"Already exists: {images[current_index]}")

def next_image(event=None):
    global current_index
    if current_index < len(images) - 1:
        current_index += 1
        show_image()

def prev_image(event=None):
    global current_index
    if current_index > 0:
        current_index -= 1
        show_image()

def key_handler(event):
    if event.char.lower() == 'z':
        copy_image()
    elif event.char.lower() == 'n':
        next_image()
    elif event.char.lower() == 'p':
        prev_image()
    elif event.char.lower() == 'q':
        root.destroy()

root.bind("<Key>", key_handler)

show_image()
root.mainloop()
