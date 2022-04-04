import random
import string


def random_string_generator(
    size=10, chars=string.ascii_lowercase + string.digits
):
    return "".join(random.choice(chars) for _ in range(size))


def unique_order_id_generator(instance):
    new_order_id = random_string_generator()

    if instance.objects.filter(order_id=new_order_id).exists():
        return unique_order_id_generator(instance)
    return new_order_id
