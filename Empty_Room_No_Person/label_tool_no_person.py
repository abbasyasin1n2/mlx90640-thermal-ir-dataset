import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from pathlib import Path
import json

root = tk.Tk()

root.title("Thermal Image Labeling Tool")
root.geometry("500x700")

title = tk.Label(
    root,
    text="Thermal Image Processing Tool",
    font=("Arial", 24, "bold")
)

title.pack(pady=(15, 5))

subtitle = tk.Label(
    root,
    text="by Saklaen Mo. Haa-mim",
    font=("Arial", 17, "italic"),
    fg="gray"
)

subtitle.pack(pady=(0, 11))

image_folder = Path("/Users/saklaen/Downloads/IR_Samples/Empty_Room_No_Person/Empty_Room_No_Person_image")

image_extensions = ["*.png", "*.jpg", "*.jpeg", "*.bmp", "*.tif", "*.tiff"]

image_list = []

for ext in image_extensions:
    image_list.extend(image_folder.glob(ext))

image_list = sorted(image_list)

labels_file = Path(__file__).parent / "Empty_Room_No_Person"

current_index = 0

if labels_file.exists():
    with open(labels_file, "r") as f:
        data = json.load(f)

    current_index = len(data.get("Empty_Room_No_Person", {}))

if len(image_list) == 0:
    messagebox.showerror("Error", "No images found in the selected folder!")
    root.destroy()
    exit()

if current_index >= len(image_list):
    current_index = len(image_list) - 1

image_path = image_list[current_index]


def load_image():
    global image_path

    image = Image.open(image_path)
    photo = ImageTk.PhotoImage(image)

    print(image.size)

    image_label.config(image=photo)
    image_label.image = photo

    image_name_label.config(text=f"Image: {image_path.stem}")

    progress_label.config(
        text=f"Progress: {current_index + 1} / {len(image_list)}"
    )


image_label = tk.Label(
    root,
    relief="solid"
)

image_label.pack(pady=20)


def toggle(button):
    if button["text"] == "0":
        button.config(text="1")
    else:
        button.config(text="0")


def save_label():
    print("Saving to Empty Room No Person...")
    print(labels_file.resolve())

    global current_index, image_path

    image_name = image_path.stem

    matrix = []

    for row in buttons:
        matrix.append([int(btn["text"]) for btn in row])

    print(matrix)

    if not labels_file.exists():
        data = {
            "Empty_Room_No_Person": {}
        }
    else:
        with open(labels_file, "r") as f:
            data = json.load(f)

        data.setdefault("Empty_Room_No_Person", {})

    data["Empty_Room_No_Person"][image_name] = matrix

    with open(labels_file, "w") as f:
        json.dump(data, f, indent=4)

    print(f"{image_name} saved!")
    print("Empty Room No Person count:", len(data["Empty_Room_No_Person"]))

    if current_index < len(image_list) - 1:
        current_index += 1
        image_path = image_list[current_index]

        load_image()

        for row in buttons:
            for btn in row:
                btn.config(text="0")
    else:
        messagebox.showinfo(
            "Completed",
            f"🎉 Congratulations!\n\nAll {len(image_list)} images have been labeled successfully."
        )

        save_button.config(state="disabled")


control_frame = tk.Frame(root)
control_frame.pack(pady=15, fill="both", expand=True)

image_name_label = tk.Label(
    control_frame,
    text="Image: Empty_Room_No_Person_0001",
    font=("Arial", 14, "bold")
)

image_name_label.pack(pady=5)

progress_label = tk.Label(
    control_frame,
    text="Progress: 0 / 0",
    font=("Arial", 12)
)

progress_label.pack(pady=5)

load_image()

matrix_label = tk.Label(
    control_frame,
    text="Binary Matrix:",
    font=("Arial", 12)
)

matrix_label.pack(pady=(10, 5))

grid_frame = tk.Frame(control_frame)
grid_frame.pack(pady=10)

headers = ["Person", "Standing", "Sitting", "Lying"]
rows = ["Left Half", "Right Half"]

buttons = []

# Column Headers
for col, text in enumerate(headers):
    label = tk.Label(
        grid_frame,
        text=text,
        font=("Arial", 11, "bold")
    )
    label.grid(row=0, column=col + 1, padx=5, pady=5)

# Rows + Buttons
for r, row_name in enumerate(rows):
    row_label = tk.Label(
        grid_frame,
        text=row_name,
        font=("Arial", 11, "bold")
    )
    row_label.grid(row=r + 1, column=0, padx=10, pady=5, sticky="e")

    row_buttons = []

    for c in range(4):
        btn = tk.Button(
            grid_frame,
            text="0",
            width=4,
            height=2,
            font=("Arial", 12),
            command=lambda b=None: None
        )

        btn.grid(row=r + 1, column=c + 1, padx=5, pady=5)

        btn.config(command=lambda b=btn: toggle(b))

        row_buttons.append(btn)

    buttons.append(row_buttons)

save_button = tk.Button(
    control_frame,
    text="Save",
    command=save_label
)

save_button.pack(pady=10)

root.mainloop()
