from PIL import Image
import pillow_heif

try:
    # Check if saving HEIF is supported
    pillow_heif.register_heif_opener() # Ensure it's registered
    if not pillow_heif.is_supported("test.heic"):
        print("HEIF/HEIC saving not supported by this Pillow-HEIF build.")
    else:
        img = Image.new("RGB", (100, 100), (255, 255, 0)) # Yellow
        img.save("test.heic", quality=90) # quality is an important param for HEIC
        print("test.heic created successfully.")
except Exception as e:
    print(f"Failed to create test.heic: {e}")
