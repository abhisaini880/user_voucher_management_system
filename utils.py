import random
import string
import base64
import math
import requests

api_key = "J2uHCbY3zqnsfo0X"
api_pass = "5jaQBxbotJ"


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


def send_sms(mobile, message, template_id):

    if not (mobile and message and template_id):
        return None
    url = (
        "https://smscounter.com/api/url_api.php?api_key="
        + api_key
        + "&pass="
        + api_pass
        + "&senderid=RBUDAN&template_id="
        + template_id
        + "&message="
        + message
        + "&dest_mobileno="
        + str(mobile)
        + "&mtype=TXT"
    )
    print(url)
    res = requests.get(url, verify=False)
    print(res.content)
    return None


def generate_message(key, value):
    template_id, message = None, None
    if key == "otp":
        template_id = "1507164976279565550"
        message = f"Your+OTP+from+Reckitt+Udaan+is+({value})"

    if key == "order":
        template_id = "1507164977266452298"
        message = f"Congratulations!+Your+order+ID+({value})+has+been+confirmed.+It+will+be+delivered+in+15+days.+For+any+support%2C+reach+out+to+us+at+helpdesk%40reckittudaan.in+or+call+us+at+0120-4602918+Team+Rbudan"
    return message, template_id
