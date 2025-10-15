import os
import shutil
import tempfile
import platform
import ctypes
from tkinter import *
from tkinter import filedialog, ttk, messagebox
from PIL import Image, ImageTk
import cv2
import numpy as np

# DPI awareness for Windows
if platform.system() == "Windows":
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except:
            pass

# Validate image
def is_image(file_path):
    try:
        with Image.open(file_path) as img:
            img.verify()
        return True
    except:
        return False
    
def is_blurry(path, threshold=100):
    """Returns True if the image is blurry based on Laplacian variance."""
    try:
        img = cv2.imread(path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        return lap_var < threshold  # lower variance = blurrier
    except:
        return False

# Categorize by resolution
def categorize_image(width, height):
    pixels = width * height
    if pixels < 480*360:
        return "Below 360p"
    elif pixels < 720*480:
        return "360p"
    elif pixels < 1280*720:
        return "480p"
    elif pixels < 1920*1080:
        return "720p"
    elif pixels < 2560*1440:
        return "1080p"
    elif pixels < 3840*2160:
        return "1440p"
    else:
        return "4K or above"

categorized = {}

# Analyze folder
def analyze_folder():
    folder = filedialog.askdirectory(title="Select Folder")
    if folder:
        files = [os.path.join(folder, f) for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
        analyze_images(files)

# Analyze selected images
def analyze_selected_images():
    files = filedialog.askopenfilenames(title="Select Images")
    if files:
        analyze_images(files)

# Core analysis
def analyze_images(file_list):
    global categorized
    for w in content_frame.winfo_children():
        w.destroy()
    categorized.clear()

    for path in file_list:
        if not is_image(path):
            continue
        try:
            with Image.open(path) as img:
                w, h = img.size
        except:
            continue
        cat = categorize_image(w, h)
        blurry = is_blurry(path)
        if blurry:
            cat += " (Blurry)"
        else:
            cat += " (Clear)"
        categorized.setdefault(cat, []).append((os.path.basename(path), path))      

    show_results()
    canvas.update_idletasks()
    canvas.config(scrollregion=canvas.bbox("all"))

# Download ZIP for category
def download_category(cat_name):
    if cat_name not in categorized or not categorized[cat_name]:
        messagebox.showwarning("No Data", f"No images in {cat_name}")
        return

    save_path = filedialog.asksaveasfilename(defaultextension=".zip",
                                             initialfile=f"{cat_name}.zip",
                                             filetypes=[("ZIP Files","*.zip")])
    if not save_path:
        return

    with tempfile.TemporaryDirectory() as tmp:
        cat_dir = os.path.join(tmp, cat_name)
        os.makedirs(cat_dir, exist_ok=True)
        for _, path in categorized[cat_name]:
            shutil.copy(path, cat_dir)
        shutil.make_archive(save_path.replace(".zip",""), "zip", tmp)

    messagebox.showinfo("Success", f"{cat_name} saved as {os.path.basename(save_path)}")

# Show results with per-category download button
def show_results():
    # Clear all existing widgets
    for w in content_frame.winfo_children():
        w.destroy()

    if not categorized:
        Label(content_frame, text="No valid images found", font=("Arial", 11)).pack(pady=20)
        return

    # ✅ Define your desired order
    category_order = ["4K or above (Clear)", "4K or above (Blurry)",
                  "1440p (Clear)", "1440p (Blurry)",
                  "1080p (Clear)", "1080p (Blurry)",
                  "720p (Clear)", "720p (Blurry)",
                  "480p (Clear)", "480p (Blurry)",
                  "360p (Clear)", "360p (Blurry)",
                  "Below 360p (Clear)", "Below 360p (Blurry)"]
    
    # Sort categories according to that order
    sorted_categories = sorted(
        categorized.items(),
        key=lambda item: category_order.index(item[0]) if item[0] in category_order else len(category_order)
    )

    # ✅ Display categories in sorted order
    for cat, files in sorted_categories:
        frame = LabelFrame(content_frame, text=cat, font=("Arial", 11, "bold"), padx=10, pady=10)
        frame.pack(fill="x", pady=10, padx=10)

        # Per-category download button
        btn = Button(
            frame,
            text=f"👇 Download {cat} ZIP",
            bg="#2196F3",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=15,
            pady=6,
            command=lambda c=cat: download_category(c)
        )
        btn.pack(pady=5)

        imgs_frame = Frame(frame)
        imgs_frame.pack(fill="x", pady=5)

        # Display thumbnails in grid
        max_cols = 5
        row = col = 0
        for name, path in files:
            try:
                img = Image.open(path)
                img = img.resize((50, 50), Image.LANCZOS)
                tk_img = ImageTk.PhotoImage(img)

                lbl = Label(imgs_frame, image=tk_img)
                lbl.image = tk_img
                lbl.grid(row=row * 2, column=col, padx=5, pady=5)

                lbl_name = Label(imgs_frame, text=name, font=("Arial", 9))
                lbl_name.grid(row=row * 2 + 1, column=col, padx=5)

                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1
            except Exception as e:
                print(f"Error loading {path}: {e}")
                continue


# UI setup
root = Tk()
root.title("Image Quality Categorizer")
root.geometry("1280x700")
root.configure(bg="#f2f2f2")
root.tk.call('tk', 'scaling', 1.5)
root.option_add("*Font","Arial 10")

title = Label(root, text="Image Quality Categorizer", font=("Arial",16,"bold"), bg="#4A90E2", fg="white", pady=12)
title.pack(fill=X)

btn_frame = Frame(root, bg="#f2f2f2")
btn_frame.pack(pady=10)

Button(btn_frame, text="📸 Select Images", bg="#FF9800", fg="white", relief=GROOVE,
       command=analyze_selected_images).pack(side=LEFT, padx=10)
Button(btn_frame, text="📁 Select Folder", bg="#4CAF50", fg="white", relief=GROOVE,
       command=analyze_folder).pack(side=LEFT, padx=10)

# Scrollable canvas
canvas_frame = Frame(root)  # Wrapper for canvas + scrollbars
canvas_frame.pack(fill=BOTH, expand=True)

canvas = Canvas(canvas_frame, bg="#f2f2f2", highlightthickness=0)
canvas.pack(side=LEFT, fill=BOTH, expand=True)

scroll_y = ttk.Scrollbar(canvas_frame, orient=VERTICAL, command=canvas.yview)
scroll_y.pack(side=RIGHT, fill=Y)

scroll_x = ttk.Scrollbar(root, orient=HORIZONTAL, command=canvas.xview)
scroll_x.pack(side=BOTTOM, fill=X)

canvas.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

content_frame = Frame(canvas, bg="#f2f2f2")
canvas.create_window((0, 0), window=content_frame, anchor="nw")

# --- Scroll binding ---
def on_mousewheel(event):
    canvas.yview_scroll(-1*(event.delta//120), "units")

def on_shift_mousewheel(event):
    canvas.xview_scroll(-1*(event.delta//120), "units")

# Update scrollable area dynamically
def update_scroll_region(event=None):
    canvas.configure(scrollregion=canvas.bbox("all"))

content_frame.bind("<Configure>", update_scroll_region)
canvas.bind_all("<MouseWheel>", on_mousewheel)
canvas.bind_all("<Shift-MouseWheel>", on_shift_mousewheel)
canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1,"units"))
canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1,"units"))

root.mainloop()