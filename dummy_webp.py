from PIL import Image
img = Image.new("RGB", (100, 100), (0, 0, 255)) # Blue
img.save("test.webp", format="WEBP")
