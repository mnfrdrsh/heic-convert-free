from PIL import Image
img = Image.new("P", (100, 100), 0) # Palette image, black
img.save("test.gif")
