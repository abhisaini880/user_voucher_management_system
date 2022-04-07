import random
import string
import base64
import math


def random_string_generator(size=10):
    return "".join(
        [
            random.choice(
                string.ascii_uppercase + string.ascii_lowercase + string.digits
            )
            for _ in range(size)
        ]
    )


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


def generate_otp():
    digits = "0123456789"
    OTP = ""
    for _ in range(4):
        OTP += digits[math.floor(random.random() * 10)]

    return OTP


def send_otp(mobile, otp):
    conn = http.client.HTTPSConnection("api.msg91.com")
    authkey = settings.AUTH_KEY
    headers = {"content-type": "application/json"}
    url = (
        "http://control.msg91.com/api/sendotp.php?otp="
        + otp
        + "&message="
        + "Your otp is "
        + otp
        + "&mobile="
        + mobile
        + "&authkey="
        + authkey
        + "&country=91"
    )
    conn.request("GET", url, headers=headers)
    res = conn.getresponse()
    data = res.read()
    print(data)
    return None
