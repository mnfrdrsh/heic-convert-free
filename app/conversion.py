import os
from typing import Iterable, Callable, Tuple
from PIL import Image, UnidentifiedImageError
import pillow_heif

# Register HEIF/HEIC opener
pillow_heif.register_heif_opener()

# Supported output formats (common ones)
SUPPORTED_OUTPUT_FORMATS = [
    "PNG", "JPEG", "GIF", "BMP", "TIFF", "WEBP"
]


def get_compatible_formats(image_obj: Image.Image) -> list:
    """Return formats compatible with the given PIL image."""
    if not image_obj:
        return []

    mode = image_obj.mode
    compatible_formats = []
    for fmt in SUPPORTED_OUTPUT_FORMATS:
        fmt_upper = fmt.upper()
        if fmt_upper in {"PNG", "WEBP", "TIFF"}:
            compatible_formats.append(fmt)
        elif fmt_upper == "JPEG":
            if mode in ("L", "RGB", "RGBA", "LA", "PA", "CMYK"):
                compatible_formats.append(fmt)
            elif mode == "P" and image_obj.palette and image_obj.palette.mode in {"L", "RGB"}:
                compatible_formats.append(fmt)
        elif fmt_upper == "BMP":
            if mode in ("L", "RGB", "RGBA", "LA", "PA", "P"):
                compatible_formats.append(fmt)
        elif fmt_upper == "GIF":
            compatible_formats.append(fmt)

    return list(dict.fromkeys(compatible_formats))


def convert_images(
    files: Iterable[str],
    output_fmt: str,
    out_folder: str,
    status_cb: Callable[[str], None] | None = None,
) -> Tuple[int, int]:
    """Convert a sequence of image files. Returns (success_count, error_count)."""

    success_count = 0
    error_count = 0
    total_files = len(list(files)) if not isinstance(files, list) else len(files)
    files_list = list(files)

    if not os.path.isdir(out_folder):
        try:
            os.makedirs(out_folder, exist_ok=True)
        except OSError as exc:
            if status_cb:
                status_cb(f"Error creating output folder: {exc}")
            return (0, len(files_list))

    for i, file_path in enumerate(files_list):
        filename = os.path.basename(file_path)
        base_name = os.path.splitext(filename)[0]
        output_filename = f"{base_name}.{output_fmt.lower()}"
        output_path = os.path.join(out_folder, output_filename)
        if status_cb:
            status_cb(f"Converting ({i+1}/{total_files}): {filename}")

        if not os.path.exists(file_path):
            error_count += 1
            if status_cb:
                status_cb(f"Skipped {filename}: not found")
            continue

        try:
            is_heic = file_path.lower().endswith((".heic", ".heif"))
            with Image.open(file_path) as img:
                try:
                    img.load()
                except Exception:
                    if is_heic:
                        heif_file = pillow_heif.read_heif(file_path)
                        img = Image.frombytes(
                            heif_file.mode,
                            heif_file.size,
                            heif_file.data,
                            "raw",
                            heif_file.mode,
                            heif_file.stride,
                        )
                current_mode = img.mode
                if is_heic and current_mode not in ("RGB", "RGBA"):
                    img = img.convert("RGB")
                    current_mode = "RGB"

                needs_flatten = False
                target_mode = "RGB"
                if output_fmt.upper() in ["JPEG", "BMP"]:
                    if current_mode in ("RGBA", "LA", "PA"):
                        needs_flatten = True
                if current_mode == "P":
                    if "transparency" in img.info:
                        img = img.convert("RGBA")
                        current_mode = "RGBA"
                        if output_fmt.upper() in ["JPEG", "BMP"]:
                            needs_flatten = True
                    elif output_fmt.upper() in ["JPEG", "BMP"]:
                        img = img.convert("RGB")
                        current_mode = "RGB"
                elif current_mode == "LA":
                    if output_fmt.upper() in ["JPEG", "BMP"]:
                        needs_flatten = True
                    else:
                        img = img.convert("RGBA")
                        current_mode = "RGBA"

                if needs_flatten:
                    bg = Image.new(target_mode, img.size, (255, 255, 255))
                    try:
                        mask = img.getchannel("A")
                        bg.paste(img, (0, 0), mask)
                        img = bg
                        current_mode = target_mode
                    except Exception:
                        img = img.convert(target_mode)
                        current_mode = target_mode
                elif output_fmt.upper() == "BMP" and current_mode != "RGB":
                    img = img.convert("RGB")
                    current_mode = "RGB"
                elif output_fmt.upper() == "JPEG" and current_mode not in ("RGB", "L", "CMYK"):
                    img = img.convert("RGB")
                    current_mode = "RGB"

                save_kwargs = {}
                if output_fmt.upper() == "JPEG":
                    save_kwargs = {"quality": 95, "optimize": True, "progressive": True}
                elif output_fmt.upper() == "PNG":
                    save_kwargs = {"optimize": True}
                elif output_fmt.upper() == "WEBP":
                    save_kwargs = {"quality": 80, "lossless": False}
                elif output_fmt.upper() == "GIF":
                    save_kwargs = {"optimize": True}
                elif output_fmt.upper() == "TIFF":
                    save_kwargs = {"compression": "tiff_lzw"}

                img.save(output_path, format=output_fmt, **save_kwargs)
                success_count += 1
        except UnidentifiedImageError:
            msg = (
                f"Cannot decode HEIC: {filename}" if file_path.lower().endswith((".heic", ".heif"))
                else f"Cannot identify image file: {filename}"
            )
            if status_cb:
                status_cb(msg)
            error_count += 1
        except Exception as exc:
            if status_cb:
                status_cb(f"Error converting {filename}: {type(exc).__name__}")
            error_count += 1

    return success_count, error_count
