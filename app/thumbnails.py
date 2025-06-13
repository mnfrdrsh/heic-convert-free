import os
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, UnidentifiedImageError

THUMBNAIL_SIZE = (100, 100)


def update_thumbnails(scrollable_frame: ttk.Frame, canvas: tk.Canvas, input_files: list) -> list:
    """Populate the scrollable_frame with thumbnails for the given files.

    Returns a list of PhotoImage references to keep alive.
    """
    for widget in scrollable_frame.winfo_children():
        widget.destroy()

    photo_refs: list[ImageTk.PhotoImage] = []

    if not input_files:
        no_files_label = ttk.Label(scrollable_frame, text="No images loaded.", style="secondary.TLabel")
        no_files_label.pack(pady=20)
        scrollable_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))
        return photo_refs

    row = col = 0
    frame_width = scrollable_frame.winfo_width() or 550
    max_cols = max(1, frame_width // (THUMBNAIL_SIZE[0] + 15))

    for file_path in input_files:
        thumb_frame = ttk.Frame(scrollable_frame, padding=2)
        thumb_frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

        filename = os.path.basename(file_path)
        max_len = 15
        display_name = (filename[:max_len] + "...") if len(filename) > max_len else filename

        try:
            img = Image.open(file_path)
            try:
                img.load()
            except Exception as exc:
                print(f"Warning loading {filename} for thumbnail: {exc}")

            img.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
            if img.mode not in ("RGB", "RGBA"):
                if img.mode == "P" and "transparency" in img.info:
                    img = img.convert("RGBA")
                else:
                    img = img.convert("RGB")

            photo_img = ImageTk.PhotoImage(img)
            img_label = ttk.Label(thumb_frame, image=photo_img)
            img_label.image = photo_img
            img_label.pack()
            name_label = ttk.Label(thumb_frame, text=display_name, anchor=tk.CENTER, wraplength=THUMBNAIL_SIZE[0])
            name_label.pack(fill=tk.X)
            photo_refs.append(photo_img)
        except UnidentifiedImageError:
            error_label = ttk.Label(
                thumb_frame,
                text=f"{display_name}\n(unidentified)",
                relief=tk.SOLID,
                width=15,
                anchor=tk.CENTER,
                justify=tk.CENTER,
                style="secondary.TLabel",
            )
            error_label.pack(ipadx=5, ipady=10)
        except FileNotFoundError:
            error_label = ttk.Label(
                thumb_frame,
                text=f"{display_name}\n(not found)",
                relief=tk.SOLID,
                width=15,
                anchor=tk.CENTER,
                justify=tk.CENTER,
                style="secondary.TLabel",
            )
            error_label.pack(ipadx=5, ipady=10)
        except Exception as exc:
            error_label = ttk.Label(
                thumb_frame,
                text=f"{display_name}\n(Error: {type(exc).__name__})",
                relief=tk.SOLID,
                width=15,
                anchor=tk.CENTER,
                justify=tk.CENTER,
                style="secondary.TLabel",
            )
            error_label.pack(ipadx=5, ipady=10)
        finally:
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    scrollable_frame.update_idletasks()
    canvas.config(scrollregion=canvas.bbox("all"))
    return photo_refs
