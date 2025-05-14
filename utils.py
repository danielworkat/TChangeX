from PIL import Image

def resize_image(input_path, output_path, size=(300, 300)):
    img = Image.open(input_path)
    img.thumbnail(size)
    img.save(output_path)
