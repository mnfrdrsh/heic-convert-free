from PIL import Image
img = Image.new("RGBA", (100, 100), (255, 0, 0, 0)) # Transparent red
img.save("test_rgba.png")
