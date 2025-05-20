from PIL import Image, ImageDraw
import os

def create_app_icon():
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
        (frame_padding, frame_padding, icon_size[0]-frame_padding, icon_size[1]-frame_padding), 
        outline=(255, 255, 255), 
        width=8
    )
    
    # Arrow symbol (conversion)
    arrow_width = 40
    center_x, center_y = icon_size[0] // 2, icon_size[1] // 2
    # Draw right-pointing arrow
    draw.polygon(
        [
            (center_x - 50, center_y - 30),  # Left point
            (center_x + 30, center_y - 30),  # Top right
            (center_x + 30, center_y - 50),  # Top arrow tip point
            (center_x + 70, center_y),       # Arrow tip
            (center_x + 30, center_y + 50),  # Bottom arrow tip point
            (center_x + 30, center_y + 30),  # Bottom right
            (center_x - 50, center_y + 30),  # Bottom left
        ],
        fill=(255, 255, 255)
    )
    
    # Save in different sizes needed for Windows
    icon_image.save("HEIC_app_icon.png")
    
    # Save as ICO file for Windows
    # Resize to different dimensions needed for Windows
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    images = []
    
    for size in sizes:
        resized_img = icon_image.resize(size, Image.Resampling.LANCZOS)
        images.append(resized_img)
    
    # Save as ICO (Windows icon format)
    icon_image.save("HEIC_app_icon.ico", format="ICO", sizes=[(x, x) for x in [16, 32, 48, 64, 128, 256]])
    
    print("Icon files created successfully.")
    
if __name__ == "__main__":
    create_app_icon() 