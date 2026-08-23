import os
import shutil
from tkinter import Tk, Label
from PIL import Image, ImageTk

# ================= CONFIG =================
IMAGE_FOLDER = r"G:\wedf\Bride\001"
COPY_TO_FOLDER = r"E:\python_bride\001"
SUPPORTED_FORMATS = (".jpg", ".jpeg", ".png", ".bmp")
MAX_SIZE = (850, 650)
# =========================================

os.makedirs(COPY_TO_FOLDER, exist_ok=True)

images = sorted([f for f in os.listdir(IMAGE_FOLDER)
                 if f.lower().endswith(SUPPORTED_FORMATS)])

current_index = 0
current_rotation = 0

zoom_levels = [1.0, 1.5, 2.0, 2.5]
zoom_index = 0

root = Tk()
root.title("Python Image Viewer")
root.geometry("900x700")

label = Label(root)
label.pack(expand=True)

# -------------------------------------------------
def load_image():
    image_path = os.path.join(IMAGE_FOLDER, images[current_index])
    img = Image.open(image_path)

    if current_rotation != 0:
        img = img.rotate(current_rotation, expand=True)

    zoom_factor = zoom_levels[zoom_index]
    if zoom_factor != 1.0:
        w, h = img.size
        img = img.resize(
            (int(w * zoom_factor), int(h * zoom_factor)),
            Image.LANCZOS
        )

    img.thumbnail(MAX_SIZE)
    return ImageTk.PhotoImage(img)

def show_image():
    global img_tk
    img_tk = load_image()
    label.config(image=img_tk)
    root.title(
        f"{images[current_index]} "
        f"({current_index+1}/{len(images)}) "
        f"Zoom:{int(zoom_levels[zoom_index]*100)}%"
    )

# -------------------------------------------------
def copy_image():
    src = os.path.join(IMAGE_FOLDER, images[current_index])
    dst = os.path.join(COPY_TO_FOLDER, images[current_index])

    if not os.path.exists(dst):
        shutil.copy2(src, dst)
        print(f"Copied: {images[current_index]}")

# -------------------------------------------------
def next_image(event=None):
    global current_index, current_rotation, zoom_index
    if current_index < len(images) - 1:
        current_index += 1
        current_rotation = 0
        zoom_index = 0
        show_image()

def prev_image(event=None):
    global current_index, current_rotation, zoom_index
    if current_index > 0:
        current_index -= 1
        current_rotation = 0
        zoom_index = 0
        show_image()

# -------------------------------------------------
def rotate_portrait(event=None):
    global current_rotation
    current_rotation = 90
    show_image()

def rotate_landscape(event=None):
    global current_rotation
    current_rotation = 0
    show_image()

# ---------------- ZOOM TOGGLE ---------------------
def toggle_zoom(event=None):
    global zoom_index
    zoom_index = (zoom_index + 1) % len(zoom_levels)
    show_image()

# -------------------------------------------------
def key_handler(event):
    if event.char.lower() == 'z':
        copy_image()
    elif event.char.lower() == 'q':
        root.destroy()

# -------- KEY BINDINGS ----------------------------
root.bind("<Left>", prev_image)
root.bind("<Right>", next_image)
root.bind("<Up>", rotate_portrait)
root.bind("<Down>", rotate_landscape)

# Shift key toggles zoom
root.bind("<Shift_L>", toggle_zoom)
root.bind("<Shift_R>", toggle_zoom)

root.bind("<Key>", key_handler)

show_image()
root.mainloop()
