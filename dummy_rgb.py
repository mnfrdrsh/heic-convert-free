from PIL import Image
img = Image.new("RGB", (100, 100), (0, 255, 0)) # Green
img.save("test_rgb.jpg")
