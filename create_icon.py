from pathlib import Path

from PIL import Image, ImageDraw


def create_app_icon(output_dir: str | Path | None = None, output_name: str = "app_icon"):
    # Create a simple image for the icon
    icon_size = (256, 256)
    background_color = (60, 141, 188)  # Blue background
    icon_image = Image.new("RGBA", icon_size, background_color)

    # Get a drawing context
    draw = ImageDraw.Draw(icon_image)

    # Draw icon elements - a simple image converter representation
    # Outer frame
    frame_padding = 50
    draw.rectangle(
        (
            frame_padding,
            frame_padding,
            icon_size[0] - frame_padding,
            icon_size[1] - frame_padding,
        ),
        outline=(255, 255, 255),
        width=8,
    )

    # Arrow symbol (conversion)
    center_x, center_y = icon_size[0] // 2, icon_size[1] // 2
    # Draw right-pointing arrow
    draw.polygon(
        [
            (center_x - 50, center_y - 30),  # Left point
            (center_x + 30, center_y - 30),  # Top right
            (center_x + 30, center_y - 50),  # Top arrow tip point
            (center_x + 70, center_y),  # Arrow tip
            (center_x + 30, center_y + 50),  # Bottom arrow tip point
            (center_x + 30, center_y + 30),  # Bottom right
            (center_x - 50, center_y + 30),  # Bottom left
        ],
        fill=(255, 255, 255),
    )

    target_dir = Path(output_dir) if output_dir else Path(__file__).resolve().parent
    target_dir.mkdir(parents=True, exist_ok=True)
    png_path = target_dir / f"{output_name}.png"
    ico_path = target_dir / f"{output_name}.ico"

    # Save PNG version of the icon
    icon_image.save(png_path)

    # Save as ICO file for Windows
    # Resize to multiple icon resolutions required on Windows
    sizes = [(s, s) for s in (16, 32, 48, 64, 128, 256)]

    # Save as ICO (Windows icon format)
    icon_image.save(ico_path, format="ICO", sizes=sizes)

    print(f"Icon files created successfully: {png_path.name}, {ico_path.name}")


if __name__ == "__main__":
    create_app_icon()
