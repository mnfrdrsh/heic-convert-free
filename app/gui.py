# -*- coding: utf-8 -*-
# Added encoding declaration for potentially wider compatibility

import tkinter as tk
from tkinter import ttk  # Themed widgets
from tkinter import filedialog, messagebox
# Make sure you are using tkinterdnd2 here after the previous fix!
from tkinterdnd2 import TkinterDnD, DND_FILES # Import TkinterDnD and the file type
from PIL import Image, UnidentifiedImageError # Pillow for image processing
import os
import threading # To keep UI responsive during conversion
import sys # Needed for theme check
import pillow_heif # <--- Import pillow-heif to register HEIC support

# Register HEIC/HEIF formats explicitly
pillow_heif.register_heif_opener()

from .conversion import SUPPORTED_OUTPUT_FORMATS, convert_images, get_compatible_formats
from .thumbnails import update_thumbnails

class ImageConverterApp(TkinterDnD.Tk): # Inherit from TkinterDnD.Tk for DND

    def __init__(self):
        super().__init__() # Initialize TkinterDnD

        self.title("Simple Image Converter")
        self.geometry("600x650")  # Increased height to show Output Settings
        self.minsize(500, 600)  # Set minimum window size

        # Add app icon for Windows
        if sys.platform == "win32":
            try:
                self.iconbitmap(default="app_icon.ico")
            except:
                pass  # Icon not found, continue without it
        
        # --- Data Storage ---
        self.input_files = []
        self.output_folder = tk.StringVar(value=os.path.expanduser("~")) # Default to home dir
        self.output_format = tk.StringVar(value=SUPPORTED_OUTPUT_FORMATS[0])
        self.thumbnail_widgets = [] # Keep track of thumbnail labels (PhotoImage objects)

        # --- UI Elements ---
        self._create_widgets()
        self._configure_drag_and_drop()
        self._update_output_format_dropdown() # Initial call after widgets are created

    def _create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 1. Drag and Drop Area
        dnd_frame = ttk.LabelFrame(main_frame, text="1. Drop Images Here", padding="10")
        dnd_frame.pack(fill=tk.X, pady=(0, 10))

        self.dnd_label = ttk.Label(
            dnd_frame,
            text="Drag & Drop Image Files Here\nor Click to Clear List", # Modified text
            relief=tk.SOLID,
            borderwidth=1,
            anchor=tk.CENTER,
            padding=20
        )
        self.dnd_label.pack(fill=tk.X, expand=True)
        # Add a click event to clear the list
        self.dnd_label.bind("<Button-1>", self._clear_file_list)

        # 2. Thumbnail Preview Area
        preview_frame = ttk.LabelFrame(main_frame, text="2. Preview", padding="10")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Reduce the height of the preview frame to make room for Output Settings
        preview_height = 250  # Set a fixed height for the preview area
        preview_frame.pack_propagate(False)  # Prevent resizing based on content
        preview_frame.configure(height=preview_height)

        # Canvas and Scrollbar for thumbnails
        self.canvas = tk.Canvas(preview_frame, borderwidth=0, background="#ffffff")
        self.scrollbar = ttk.Scrollbar(preview_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas) # Frame inside canvas

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Bind mouse wheel for scrolling (cross-platform)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel) # Windows/macOS
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)   # Linux (scroll up)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)   # Linux (scroll down)


        # 3. Output Settings
        output_settings_frame = ttk.LabelFrame(main_frame, text="3. Output Settings", padding="10")
        output_settings_frame.pack(fill=tk.X, pady=(0, 10))

        # Output Folder
        folder_frame = ttk.Frame(output_settings_frame)
        folder_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(folder_frame, text="Output Folder:").pack(side=tk.LEFT, padx=(0, 5))
        folder_entry = ttk.Entry(folder_frame, textvariable=self.output_folder, state='readonly')
        folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        browse_button = ttk.Button(folder_frame, text="Browse...", command=self._browse_output_folder)
        browse_button.pack(side=tk.LEFT)

        # Output Format
        format_frame = ttk.Frame(output_settings_frame)
        format_frame.pack(fill=tk.X)
        ttk.Label(format_frame, text="Output Format:").pack(side=tk.LEFT, padx=(0, 5))
        format_combo = ttk.Combobox(
            format_frame,
            textvariable=self.output_format,
            values=SUPPORTED_OUTPUT_FORMATS,
            state='readonly', # Prevent typing custom values
            width=10
        )
        self.format_combo = format_combo # Store as instance variable
        self.format_combo.pack(side=tk.LEFT)

        # 4. Convert Button & Status
        action_frame = ttk.Frame(main_frame, padding="5")
        action_frame.pack(fill=tk.X)

        self.status_label = ttk.Label(action_frame, text="Ready. Drop images.", anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.convert_button = ttk.Button(action_frame, text="Convert", command=self._start_conversion_thread, state=tk.DISABLED)
        self.convert_button.pack(side=tk.RIGHT)

    def _configure_drag_and_drop(self):
        # Register the DND label to accept file drops
        self.dnd_label.drop_target_register(DND_FILES)
        self.dnd_label.dnd_bind('<<Drop>>', self._handle_drop)

    def _handle_drop(self, event):
        # event.data contains a string of file paths, possibly wrapped in braces {}
        try:
            files_str = self.tk.splitlist(event.data) # Use tk.splitlist to handle paths with spaces
        except tk.TclError:
            # Handle potential errors during path splitting (e.g., very unusual characters)
             messagebox.showerror("Drop Error", "Could not parse the dropped file paths.")
             return

        new_files = []
        skipped_non_image = 0
        skipped_other = 0
        skipped_duplicates = 0

        for f in files_str:
            # Normalize path (optional, but can help consistency)
            f_norm = os.path.normpath(f)
            if os.path.isfile(f_norm): # Check if it's actually a file
                try:
                    # Attempt to open the image to check if it's a valid image format
                    with Image.open(f_norm) as img:
                        img.load() # Actually load image data to catch more errors

                    # If successful, and not a duplicate, add to new_files
                    if f_norm not in self.input_files:
                        new_files.append(f_norm)
                    else:
                        skipped_duplicates += 1
                        print(f"Skipping duplicate file: {os.path.basename(f_norm)}")

                except UnidentifiedImageError:
                    skipped_non_image += 1
                    print(f"Skipping unsupported image file: {os.path.basename(f_norm)}")
                except FileNotFoundError: # Should ideally be caught by os.path.isfile, but good to have
                    skipped_other += 1
                    print(f"Skipping (file not found during open): {f_norm}")
                except Exception as e: # Catch other potential PIL errors
                    skipped_other += 1
                    print(f"Skipping file due to other error during open ({type(e).__name__}): {os.path.basename(f_norm)}")
            else:
                skipped_other += 1 # This handles directories or other non-file items
                print(f"Skipping item (not a file or not found): {f_norm}")

        if new_files:
            self.input_files.extend(new_files)
            status_msg = f"Added {len(new_files)} image(s)." # Changed "file(s)" to "image(s)"
            if skipped_duplicates > 0:
                 status_msg += f" Skipped {skipped_duplicates} duplicate(s)."
            if skipped_non_image > 0:
                 status_msg += f" Skipped {skipped_non_image} unsupported format(s)." # Changed message
            if skipped_other > 0:
                status_msg += f" Skipped {skipped_other} other item(s)."
            status_msg += f" Total: {len(self.input_files)}"
            self.status_label.config(text=status_msg)
            # Update thumbnails *after* adding files
            self._update_thumbnails()
            self._update_output_format_dropdown() # Update dropdown based on new file list
            self._update_convert_button_state()
        else:
            # Provide feedback even if no *new* files were added
            # Even if no new files, the list might have changed (e.g. only duplicates dropped)
            # so an update to the dropdown might still be relevant if list went from 1 to 0.
            self._update_output_format_dropdown() # Update dropdown
            status_msg = "No new valid images found in drop." # Changed message
            if skipped_duplicates > 0:
                 status_msg += f" {skipped_duplicates} duplicate(s)."
            if skipped_non_image > 0:
                 status_msg += f" {skipped_non_image} unsupported format(s)." # Changed message
            if skipped_other > 0:
                 status_msg += f" {skipped_other} other item(s)."
            self.status_label.config(text=status_msg)


    def _clear_file_list(self, event=None):
        """Clears the input file list and thumbnails."""
        if not self.input_files:
            self.status_label.config(text="List already empty.")
            return # Nothing to clear

        confirmed = messagebox.askyesno("Clear List", f"Are you sure you want to clear the list of {len(self.input_files)} image(s)?")
        if confirmed:
            self.input_files = []
            self._update_thumbnails() # This clears the display
            self._update_output_format_dropdown() # Update dropdown as file list is now empty
            self.status_label.config(text="List cleared. Drop new images.")
            self._update_convert_button_state()

    def _update_output_format_dropdown(self):
        """
        Updates the output format Combobox based on the number and type of input files.
        """
        current_selection = self.output_format.get()
        
        if len(self.input_files) == 1:
            file_path = self.input_files[0]
            compatible_formats = []
            try:
                with Image.open(file_path) as img:
                    img.load()  # Ensure image data is loaded
                    compatible_formats = get_compatible_formats(img)
            except Exception as e:
                print(f"Error opening image {file_path} for format compatibility check: {e}")
                # Fallback to all supported formats if image can't be opened/read for mode
                compatible_formats = list(SUPPORTED_OUTPUT_FORMATS)

            if not compatible_formats: # If _get_compatible_formats returned empty (should not happen with current logic but good check)
                display_formats = list(SUPPORTED_OUTPUT_FORMATS)
            else:
                display_formats = compatible_formats
            
            self.format_combo['values'] = display_formats
            
            if current_selection not in display_formats or not current_selection:
                if display_formats:
                    self.output_format.set(display_formats[0])
                elif SUPPORTED_OUTPUT_FORMATS: # Should always be true
                     self.output_format.set(SUPPORTED_OUTPUT_FORMATS[0]) # Fallback if display_formats is somehow empty
        else: # Zero or multiple files
            self.format_combo['values'] = SUPPORTED_OUTPUT_FORMATS
            if current_selection not in SUPPORTED_OUTPUT_FORMATS or not current_selection:
                if SUPPORTED_OUTPUT_FORMATS: # Should always be true
                    self.output_format.set(SUPPORTED_OUTPUT_FORMATS[0])


    def _update_thumbnails(self):
        self.thumbnail_widgets = update_thumbnails(
            self.scrollable_frame, self.canvas, self.input_files
        )


    def _browse_output_folder(self):
        # Use current output folder as starting point if valid, else user's home
        initial_dir = self.output_folder.get() if os.path.isdir(self.output_folder.get()) else os.path.expanduser("~")
        folder_selected = filedialog.askdirectory(initialdir=initial_dir, title="Select Output Folder")
        if folder_selected: # Only update if a folder was actually selected
            self.output_folder.set(folder_selected)
            self.status_label.config(text=f"Output folder set.") # Keep it short
            self._update_convert_button_state()

    def _update_convert_button_state(self):
        """Enable convert button only if files are loaded and output folder is valid."""
        state = tk.DISABLED # Default to disabled
        if self.input_files:
            out_folder = self.output_folder.get()
            if out_folder and os.path.isdir(out_folder): # Check it exists and is a directory
                 state = tk.NORMAL

        self.convert_button.config(state=state)


    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling for the canvas."""
        # Determine scroll amount (platform dependent)
        delta = 0
        if sys.platform == "darwin": # macOS needs different handling
            delta = event.delta
        elif event.num == 5 or event.delta < 0: # Scroll down (Linux/Windows)
            delta = 1
        elif event.num == 4 or event.delta > 0: # Scroll up (Linux/Windows)
            delta = -1

        # Check if the scroll event happened over the canvas or its children
        # Usewinfo_containing to find the widget under the cursor at event time
        widget_under_mouse = self.winfo_containing(event.x_root, event.y_root)
        # Check if the widget is the canvas or inside the scrollable frame
        current_widget = widget_under_mouse
        while current_widget is not None:
             if current_widget == self.canvas:
                 if sys.platform == "darwin":
                     self.canvas.yview_scroll(-1 * delta, "units")
                 else:
                     self.canvas.yview_scroll(delta, "units")
                 break # Stop searching up the hierarchy
             # Check if the parent is the scrollable frame (direct child)
             try:
                 parent = current_widget.winfo_parent()
                 if parent == str(self.scrollable_frame): # Compare widget paths
                      if sys.platform == "darwin":
                          self.canvas.yview_scroll(-1 * delta, "units")
                      else:
                          self.canvas.yview_scroll(delta, "units")
                      break
                 # Go up one level
                 current_widget = self.nametowidget(parent)
             except (tk.TclError, KeyError): # Handle cases where parent isn't a known widget
                 break


    def _start_conversion_thread(self):
        """Starts the conversion process in a separate thread to keep the UI responsive."""
        if not self.input_files:
            messagebox.showwarning("No Files", "Please add images to convert first.")
            return
        out_folder = self.output_folder.get()
        if not out_folder or not os.path.isdir(out_folder):
             messagebox.showwarning("Invalid Output Folder", "Please select a valid output folder.")
             # Try browsing again automatically
             # self._browse_output_folder()
             return

        self.convert_button.config(state=tk.DISABLED) # Disable button during conversion
        self.status_label.config(text="Starting conversion...")

        # Make a copy of the list for the thread to work on
        files_to_convert = list(self.input_files)

        # Create and start the thread
        conversion_thread = threading.Thread(
            target=self._run_conversion,
            args=(files_to_convert,),  # Pass the copy of the list
            daemon=True)
        conversion_thread.start()

    def _run_conversion(self, files):
        def cb(msg):
            self.after(0, lambda m=msg: self.status_label.config(text=m))
        success, error = convert_images(files, self.output_format.get(), self.output_folder.get(), cb)
        final_status = f"Conversion finished: {success} succeeded, {error} failed."
        self.after(0, lambda: self.status_label.config(text=final_status))
        self.after(0, self._update_convert_button_state)


