import random
import string
import base64


def random_string_generator(
    size=10, chars=string.ascii_lowercase + string.digits
):
    return "".join(random.choice(chars) for _ in range(size))


def unique_order_id_generator(instance):
    new_order_id = random_string_generator()

    if instance.objects.filter(order_id=new_order_id).exists():
        return unique_order_id_generator(instance)
    return new_order_id


def convert_image_to_binary(image_path):
    image_path = "." + str(image_path)
    image_data = None
    with open(image_path, "rb") as image_file:
        image_data = base64.b64encode(image_file.read()).decode("utf-8")

    return image_data
