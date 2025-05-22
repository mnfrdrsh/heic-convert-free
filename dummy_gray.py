from PIL import Image
img = Image.new("L", (100, 100), 128) # Mid-gray
img.save("test_grayscale.png")
