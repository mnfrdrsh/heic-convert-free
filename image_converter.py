# -*- coding: utf-8 -*-
# Added encoding declaration for potentially wider compatibility

import tkinter as tk
from tkinter import ttk  # Themed widgets
from tkinter import filedialog, messagebox
# Make sure you are using tkinterdnd2 here after the previous fix!
from tkinterdnd2 import TkinterDnD, DND_FILES # Import TkinterDnD and the file type
from PIL import Image, ImageTk, UnidentifiedImageError # Pillow for image processing
import os
import threading # To keep UI responsive during conversion
import sys # Needed for theme check
import pillow_heif # <--- Import pillow-heif to register HEIC support

# Register HEIC/HEIF formats explicitly
pillow_heif.register_heif_opener()

# Supported output formats (common ones) - Pillow supports more!
SUPPORTED_OUTPUT_FORMATS = [
    "PNG", "JPEG", "GIF", "BMP", "TIFF", "WEBP"
]
THUMBNAIL_SIZE = (100, 100)

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
                    compatible_formats = self._get_compatible_formats(img)
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
        # Clear existing thumbnails from the scrollable frame
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.thumbnail_widgets = [] # Clear the PhotoImage references

        if not self.input_files:
            no_files_label = ttk.Label(self.scrollable_frame, text="No images loaded.", style="secondary.TLabel")
            no_files_label.pack(pady=20)
            # Ensure scroll region updates even when empty
            self.scrollable_frame.update_idletasks()
            self.canvas.config(scrollregion=self.canvas.bbox("all"))
            return

        # Create new thumbnails
        row, col = 0, 0
        # Make calculation more robust for initial state
        frame_width = self.scrollable_frame.winfo_width()
        if frame_width <= 0 : frame_width = 550 # Estimate if not drawn yet
        max_cols = max(1, frame_width // (THUMBNAIL_SIZE[0] + 15)) # Adjusted spacing slightly

        for file_path in self.input_files:
            thumb_frame = ttk.Frame(self.scrollable_frame, padding=2)
            thumb_frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

            filename = os.path.basename(file_path)
            max_len = 15 # Max length for display name
            display_name = (filename[:max_len] + '...') if len(filename) > max_len else filename

            try:
                # Open image (will use pillow-heif if available for HEIC)
                img = Image.open(file_path)

                # --- Thumbnail Creation ---
                # Load image data before thumbnailing (good practice, esp for HEIC)
                try:
                    img.load()
                except Exception as load_err:
                    print(f"Warning: Could not fully load image data for thumbnail {filename}: {load_err}")
                    # Continue anyway...

                img.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS) # High-quality downsampling

                # Ensure thumbnail is in a displayable mode (RGB/RGBA)
                if img.mode not in ('RGB', 'RGBA'):
                    # Handle palette transparency before converting
                    if img.mode == 'P' and 'transparency' in img.info:
                        img = img.convert('RGBA')
                    else:
                        img = img.convert('RGB')


                # Important: Keep a reference to the PhotoImage object!
                photo_img = ImageTk.PhotoImage(img)

                # Create label to display image
                img_label = ttk.Label(thumb_frame, image=photo_img)
                img_label.image = photo_img # Keep reference!
                img_label.pack()

                # Add filename label below thumbnail
                name_label = ttk.Label(thumb_frame, text=display_name, anchor=tk.CENTER, wraplength=THUMBNAIL_SIZE[0])
                name_label.pack(fill=tk.X)

                self.thumbnail_widgets.append(photo_img) # Store reference

            except UnidentifiedImageError:
                 print(f"Error: Cannot identify image file (thumbnail): {filename}")
                 # REMOVED height=...
                 error_label = ttk.Label(thumb_frame, text=f"{display_name}\n(unidentified)", relief=tk.SOLID, width=15, anchor=tk.CENTER, justify=tk.CENTER, style="secondary.TLabel")
                 error_label.pack(ipadx=5, ipady=10) # Use padding instead of height
            except FileNotFoundError:
                 print(f"Error: File not found (thumbnail): {filename}")
                 # REMOVED height=...
                 error_label = ttk.Label(thumb_frame, text=f"{display_name}\n(not found)", relief=tk.SOLID, width=15, anchor=tk.CENTER, justify=tk.CENTER, style="secondary.TLabel")
                 error_label.pack(ipadx=5, ipady=10)
            except Exception as e:
                print(f"Error creating thumbnail for {filename}: {e}")
                # REMOVED height=...
                error_label = ttk.Label(thumb_frame, text=f"{display_name}\n(Error: {type(e).__name__})", relief=tk.SOLID, width=15, anchor=tk.CENTER, justify=tk.CENTER, style="secondary.TLabel")
                error_label.pack(ipadx=5, ipady=10)
            finally:
                 # Always update grid position
                 col += 1
                 if col >= max_cols:
                    col = 0
                    row += 1


        # Update scrollregion after adding all thumbnails
        self.scrollable_frame.update_idletasks() # Ensure widgets are placed
        self.canvas.config(scrollregion=self.canvas.bbox("all"))


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

    def _get_compatible_formats(self, image_obj):
        """
        Determines which of the SUPPORTED_OUTPUT_FORMATS are compatible
        with the mode of the given PIL Image object.
        """
        if not image_obj:
            return []

        compatible_formats = []
        mode = image_obj.mode

        # Ensure SUPPORTED_OUTPUT_FORMATS is accessible
        # (it's a global constant in this file)
        for fmt in SUPPORTED_OUTPUT_FORMATS:
            fmt_upper = fmt.upper() # Work with uppercase for consistency

            if fmt_upper == "PNG":
                # PNG supports a wide range of modes, including those with alpha.
                compatible_formats.append(fmt)
            elif fmt_upper == "WEBP":
                # WebP supports many modes, including lossy/lossless and alpha.
                compatible_formats.append(fmt)
            elif fmt_upper == "TIFF":
                # TIFF is very versatile and supports most modes.
                compatible_formats.append(fmt)
            elif fmt_upper == "JPEG":
                # App flattens 'RGBA', 'LA', 'PA' to 'RGB'.
                # JPEG natively supports 'L', 'RGB', 'CMYK'.
                if mode in ('L', 'RGB', 'RGBA', 'LA', 'PA', 'CMYK'):
                    compatible_formats.append(fmt)
                # Grayscale 'P' images can often be saved as JPEG (Pillow handles conversion)
                elif mode == 'P' and image_obj.palette and image_obj.palette.mode == 'L':
                    compatible_formats.append(fmt)
                # RGB 'P' images can often be saved as JPEG
                elif mode == 'P' and image_obj.palette and image_obj.palette.mode == 'RGB':
                    compatible_formats.append(fmt)

            elif fmt_upper == "BMP":
                # BMP primarily supports 'L', 'RGB'.
                # App flattens 'RGBA', 'LA', 'PA' to 'RGB'.
                # Pillow converts 'P' to 'RGB' for BMP.
                if mode in ('L', 'RGB', 'RGBA', 'LA', 'PA', 'P'):
                    compatible_formats.append(fmt)
            elif fmt_upper == "GIF":
                # GIF works best with 'P' mode. Pillow handles conversion from other modes.
                # All modes can generally be converted to GIF, though quality/color loss can occur.
                compatible_formats.append(fmt)

        return list(dict.fromkeys(compatible_formats)) # Remove duplicates

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
            target=self._convert_images,
            args=(files_to_convert,), # Pass the copy of the list
            daemon=True)
        conversion_thread.start()

    def _convert_images(self, files_to_process): # Accept the list as argument
        """The actual image conversion logic (runs in a separate thread)."""
        output_fmt = self.output_format.get()
        out_folder = self.output_folder.get()
        success_count = 0
        error_count = 0

        # Double check output folder exists right before conversion starts
        # This check is less critical now due to pre-check, but good safeguard
        if not os.path.isdir(out_folder):
            # It's unlikely to reach here if _start_conversion_thread checks correctly
            # But handle it just in case.
            try:
                os.makedirs(out_folder, exist_ok=True)
            except OSError as e:
                self.after(0, lambda: messagebox.showerror("Error", f"Output folder vanished or could not be created:\n{out_folder}\n{e}"))
                self.after(0, lambda: self.status_label.config(text="Error with output folder."))
                self.after(0, lambda: self._update_convert_button_state())
                return

        total_files = len(files_to_process)

        for i, file_path in enumerate(files_to_process):
            filename = os.path.basename(file_path)
            base_name = os.path.splitext(filename)[0]
            output_filename = f"{base_name}.{output_fmt.lower()}"
            output_path = os.path.join(out_folder, output_filename)

            # Update status label from thread via 'after'
            # Ensure lambda captures current values correctly
            self.after(0, lambda i=i, total=total_files, fn=filename: self.status_label.config(
                text=f"Converting ({i+1}/{total}): {fn[:30]}{'...' if len(fn)>30 else ''}" # Truncate long names
            ))

            # Check if input file still exists
            if not os.path.exists(file_path):
                 error_count += 1
                 print(f"Error: Input file vanished before conversion: {filename}")
                 self.after(0, lambda idx=i, total=total_files, fn=filename: self.status_label.config(
                    text=f"Skipped ({idx+1}/{total}): {fn[:30]}{'...' if len(fn)>30 else ''} (Not found)"
                 ))
                 continue # Skip to the next file


            try:
                # Special handling for HEIC/HEIF files
                is_heic = file_path.lower().endswith(('.heic', '.heif'))
                
                # --- Open Image ---
                with Image.open(file_path) as img:
                    # Force image loading to ensure data is accessible
                    try:
                        img.load()
                    except Exception as load_err:
                        print(f"Warning: Could not fully load image data for {filename} before conversion: {load_err}")
                        if is_heic:
                            # Try reloading with pillow_heif directly for HEIC files
                            try:
                                heif_file = pillow_heif.read_heif(file_path)
                                img = Image.frombytes(
                                    heif_file.mode, 
                                    heif_file.size, 
                                    heif_file.data,
                                    "raw", 
                                    heif_file.mode, 
                                    heif_file.stride
                                )
                            except Exception as heif_err:
                                print(f"Error: Failed to load HEIC with direct method: {heif_err}")
                                raise # Re-raise to be caught by outer exception handler

                    # --- Handle Transparency/Mode Conversion ---
                    # Make sure HEIC images are in a compatible mode (usually RGB)
                    if is_heic and img.mode not in ('RGB', 'RGBA'):
                        print(f"Converting HEIC from mode {img.mode} to RGB")
                        img = img.convert('RGB')
                        current_mode = 'RGB'
                    else:
                        current_mode = img.mode

                    needs_flattening = False
                    target_mode = 'RGB' # Default target for formats without alpha

                    # Determine if flattening is needed based on OUTPUT format
                    if output_fmt.upper() in ['JPEG', 'BMP']:
                        if current_mode in ('RGBA', 'LA', 'PA'):
                             needs_flattening = True
                        target_mode = 'RGB' # JPEG/BMP need RGB

                    # Convert Palette images first if necessary
                    if current_mode == 'P':
                        if 'transparency' in img.info:
                            img = img.convert('RGBA') # Convert to RGBA first to preserve transparency
                            current_mode = 'RGBA' # Update current mode
                            # Re-evaluate flattening if target is JPEG/BMP
                            if output_fmt.upper() in ['JPEG', 'BMP']:
                                needs_flattening = True
                        else:
                             # Convert P to RGB if target is JPEG/BMP, or keep as P if target supports it (like PNG, GIF)
                             if output_fmt.upper() in ['JPEG', 'BMP']:
                                img = img.convert('RGB')
                                current_mode = 'RGB'
                             # else: leave as P for PNG/GIF saving

                    # Convert Luminance+Alpha if necessary
                    elif current_mode == 'LA':
                        if output_fmt.upper() in ['JPEG', 'BMP']:
                            needs_flattening = True
                            target_mode = 'RGB'
                        else: # Convert to RGBA for other formats supporting alpha
                             img = img.convert('RGBA')
                             current_mode = 'RGBA'


                    # Apply flattening AFTER potential mode conversions above
                    if needs_flattening:
                        bg_color = (255, 255, 255) # White background
                        if current_mode in ('RGBA', 'LA', 'PA'): # Check mode *after* potential conversion
                             try:
                                # Create a new background image in the target mode (usually RGB)
                                bg = Image.new(target_mode, img.size, bg_color)
                                # Try to get alpha channel as mask
                                mask = None
                                try:
                                     mask = img.getchannel('A')
                                except (ValueError, IndexError, KeyError): # KeyError added for safety
                                     print(f"Warning: Could not get alpha channel for {filename} despite mode {current_mode}. Flattening without mask.")
                                     # Convert dropping alpha if mask failed
                                     img = img.convert(target_mode)
                                     current_mode = target_mode

                                if mask:
                                     # Paste using alpha mask onto background
                                     bg.paste(img, (0,0), mask)
                                     img = bg # Replace img with the flattened version
                                     current_mode = target_mode
                                # else: img was already converted if mask failed

                             except Exception as flatten_err:
                                  print(f"Error during flattening for {filename}: {flatten_err}. Trying simple convert.")
                                  img = img.convert(target_mode) # Fallback to simple conversion
                                  current_mode = target_mode
                        else:
                             # If somehow needs_flattening is true but mode isn't RGBA/LA/PA, just convert
                             img = img.convert(target_mode)
                             current_mode = target_mode


                    # Final mode check if not flattened but target needs specific mode (e.g., BMP often needs RGB)
                    if not needs_flattening:
                         if output_fmt.upper() == 'BMP' and current_mode != 'RGB':
                             # Simple BMP usually wants RGB
                              try:
                                   img = img.convert('RGB')
                                   current_mode = 'RGB'
                              except ValueError:
                                   print(f"Warning: Could not convert mode {current_mode} to RGB for BMP output of {filename}. Saving might fail.")
                         elif output_fmt.upper() == 'JPEG' and current_mode not in ('RGB', 'L', 'CMYK'):
                              # JPEG usually wants RGB, L (grayscale), or CMYK. Prefer RGB.
                               try:
                                    img = img.convert('RGB')
                                    current_mode = 'RGB'
                               except ValueError:
                                    print(f"Warning: Could not convert mode {current_mode} to RGB for JPEG output of {filename}. Saving might fail.")


                    # --- Save the image ---
                    save_kwargs = {}
                    if output_fmt.upper() == 'JPEG':
                        save_kwargs['quality'] = 95 # Good quality default for JPEG
                        save_kwargs['optimize'] = True
                        save_kwargs['progressive'] = True # Often better for web
                         # Ensure image is in a savable mode for JPEG
                        if current_mode not in ('RGB', 'L', 'CMYK'):
                             print(f"Warning: Converting mode {current_mode} to RGB for JPEG save of {filename}")
                             img = img.convert('RGB')
                    elif output_fmt.upper() == 'PNG':
                         save_kwargs['optimize'] = True
                    elif output_fmt.upper() == 'WEBP':
                        save_kwargs['quality'] = 80 # Good default for lossy WebP
                        save_kwargs['lossless'] = False # Default to lossy
                        # Consider lossless for images with alpha?
                        # if current_mode in ('RGBA', 'LA', 'PA'): save_kwargs['lossless'] = True
                    elif output_fmt.upper() == 'GIF':
                        # Pillow handles conversion to Palette ('P') mode if needed
                         save_kwargs['optimize'] = True
                    elif output_fmt.upper() == 'TIFF':
                        save_kwargs['compression'] = 'tiff_lzw' # Common lossless compression

                    # Ensure output directory still exists before saving
                    if os.path.isdir(out_folder):
                        img.save(output_path, format=output_fmt, **save_kwargs)
                        success_count += 1
                    else:
                         # This should be rare if initial checks pass
                         error_count += 1
                         print(f"Error: Output directory vanished before saving {output_filename}")
                         self.after(0, lambda fn=filename: self.status_label.config(text=f"Error saving {fn}: Output dir gone."))


            except UnidentifiedImageError:
                error_count += 1
                if file_path.lower().endswith(('.heic', '.heif')):
                     msg = f"Error: Cannot identify/decode HEIC: {filename}. Check libheif install/PATH?"
                else:
                     msg = f"Error: Cannot identify image file: {filename}"
                print(msg)
                # Update status bar briefly using lambda to capture current filename
                self.after(0, lambda status=msg: self.status_label.config(text=status))
            except (FileNotFoundError, IOError, ValueError, OSError, MemoryError, Exception) as e:
                error_count += 1
                err_type = type(e).__name__
                current_image_mode = 'unknown'
                if 'img' in locals() and hasattr(img, 'mode'):
                    current_image_mode = img.mode

                # Enhanced console print
                print(f"Error converting {filename} to {output_fmt} (mode: {current_image_mode}): ({err_type}) {e}")

                # Enhanced user message for status label
                user_message = f"Error saving {filename} as {output_fmt}: {err_type}."
                # More specific advice for common save issues
                if isinstance(e, (ValueError, OSError, MemoryError)): # MemoryError included as it can relate to format/size
                    user_message = (
                        f"Failed to save {filename} (mode: {current_image_mode}) as {output_fmt}. "
                        f"Try a more compatible format like PNG, WEBP, or TIFF, or check for sufficient disk space/memory."
                    )
                
                # Truncate filename for display in status bar to avoid overly long messages
                display_filename = (filename[:25] + '...') if len(filename) > 25 else filename
                # Update status bar briefly using lambda, ensuring variables are captured correctly
                # Rebuild the user_message for the lambda to ensure it's concise for the status bar
                # if the detailed one is too long.
                # For this case, let's try to keep the specific advice if possible,
                # the status bar will truncate if needed.
                
                # If the error is specifically about saving, the user_message is already tailored.
                # Let's ensure the lambda captures the current user_message.
                self.after(0, lambda um=user_message, dfn=display_filename: self.status_label.config(
                    text=um # Use the more detailed message directly
                ))


        # Update UI after finishing (using self.after to run in main thread)
        final_status = f"Conversion finished: {success_count} succeeded, {error_count} failed."
        self.after(0, lambda: self.status_label.config(text=final_status))
        self.after(0, lambda: self._update_convert_button_state()) # Re-enable button if conditions still met


# --- Main Execution Block ---
if __name__ == "__main__":
    # Explicitly register HEIF opener
    pillow_heif.register_heif_opener()
    
    app = ImageConverterApp()

    # Apply a theme
    style = ttk.Style()
    available_themes = style.theme_names()
    # print("Available themes:", available_themes) # For debugging themes

    preferred_themes = {
        'win32': ['vista', 'xpnative', 'clam', 'alt', 'default'],
        'darwin': ['aqua', 'clam', 'alt', 'default'],
        'linux': ['clam', 'alt', 'default', 'classic'] # Or other specific Linux themes if known
    }
    platform_key = 'linux' # Default
    if sys.platform == "win32": platform_key = 'win32'
    elif sys.platform == "darwin": platform_key = 'darwin'

    chosen_theme = None
    for theme in preferred_themes.get(platform_key, ['clam', 'default']):
        if theme in available_themes:
            try:
                 style.theme_use(theme)
                 chosen_theme = theme
                 print(f"Using theme: {theme}")
                 break
            except tk.TclError:
                 continue # Try next theme

    if not chosen_theme:
        print(f"Could not set preferred theme, using default: {style.theme_use()}")


    # Custom style for placeholder text in thumbnail area
    style.configure("secondary.TLabel", foreground="grey") # Style for placeholder/error text
    # Style for the main drop label (optional)
    # style.configure("Drop.TLabel", background="lightgrey", borderwidth=2, relief="solid")
    # self.dnd_label.config(style="Drop.TLabel") # Apply if style defined

    app.mainloop()
