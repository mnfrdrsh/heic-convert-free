import sys
import tkinter as tk
from tkinter import ttk
import pillow_heif

from app import ImageConverterApp


if __name__ == "__main__":
    pillow_heif.register_heif_opener()

    app = ImageConverterApp()

    style = ttk.Style()
    available_themes = style.theme_names()
    preferred = {
        'win32': ['vista', 'xpnative', 'clam', 'alt', 'default'],
        'darwin': ['aqua', 'clam', 'alt', 'default'],
        'linux': ['clam', 'alt', 'default', 'classic']
    }
    key = 'linux'
    if sys.platform == 'win32':
        key = 'win32'
    elif sys.platform == 'darwin':
        key = 'darwin'

    for theme in preferred.get(key, ['clam', 'default']):
        if theme in available_themes:
            try:
                style.theme_use(theme)
                break
            except tk.TclError:
                continue

    style.configure("secondary.TLabel", foreground="grey")
    app.mainloop()
