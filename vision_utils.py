import base64

def encode_image(image_file):
    if image_file:
        return base64.b64encode(image_file.getvalue()).decode("utf-8")
    return None