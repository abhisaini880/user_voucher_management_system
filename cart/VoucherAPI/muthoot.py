from django.conf import settings
import requests
from json import dumps
from cart.models import VoucherAPITokens

from cart.serializers import TokenSerializer

api_tokens = settings.MUTHOOT_API_TOKENS


class MuthootAPI:
    def __init__(self):
        self.token_data = VoucherAPITokens.objects.get(brand="Muthoot")
        self.identifier = api_tokens.get("identifier")
        self.clientcode = api_tokens.get("clientcode")
        self.username = api_tokens.get("username")
        self.password = api_tokens.get("password")
        self.party_code = api_tokens.get("party_code")
        self.auth_token = self.token_data.token
        self.error = None

    def generate_auth_token(self):
        """
        Generate the Auth token using Muthoot API if existing token is expired
        """

        try:
            url = "https://seaerpnxt.app/api/SEAapi/ApiValidateUser"
            headers = {
                "identifier": self.identifier,
                "clientcode": self.clientcode,
            }

            data = {
                "UserName": self.username,
                "Password": self.password,
                "DateFormat": "dd/MM/yyyy",
                "TimeZone": "+05:30",
            }

            response = requests.post(url=url, headers=headers, json=data)

            if response.status_code == 200:
                response = response.json()

                if response.get("success") == 1:
                    self.auth_token = response.get("data")
                    updated_data = {"token": self.auth_token}

                    serializer = TokenSerializer(
                        self.token_data, data=updated_data, partial=True
                    )
                    if serializer.is_valid():
                        serializer.save()

                        return None

                else:
                    self.error = response.get("error")

            else:
                self.error = f"Received status code - {response.status_code}"

        except Exception as error:
            print(f"Error in generating Muthoot API Token")
            print(str(error))
            self.error = "Error in generating Muthoot API Token"

    def place_order(
        self, order_id: str, order_value: int, order_details: list
    ):
        """
        Place order for vouchers

        Args:
            order_id (str): Order id
            order_value (int): Total order value
            order_details (list): Voucher details
        """
        print("inside place order")
        voucher_list = []
        try:

            url = "https://seaerpnxt.app/api/SEAapi/ManageMuthoot"

            headers = {"Authorization": self.auth_token}

            payload = {
                "APIName": "UPLOAD-GV-ORDER",
                "PartyCode": self.party_code,
                "OrderNo": order_id,
                "OrderValue": order_value,
                "OrderDetail": order_details,
            }

            response = requests.post(url=url, headers=headers, json=payload)
            if response.status_code == 401:
                # Auth token is expired, regenerate it
                self.generate_auth_token()
                headers["Authorization"] = self.auth_token
                response = requests.post(
                    url=url, headers=headers, json=payload
                )

            if response.status_code == 200:
                response = response.json()
                if response.get("success") == 1:
                    voucher_data = response.get("data", {}).get("OrderDetail")
                    for voucher in voucher_data:
                        voucher_list.append(voucher.get("VoucherNo"))

                    return voucher_list

                else:
                    self.error = response.get("error")

            else:
                self.error = f"Received status code - {response.status_code}"

            return voucher_list

        except Exception as error:
            print(f"Error in generating Muthoot API Token")
            print(str(error))
            self.error = "Error in generating Muthoot API Token"
            return voucher_list
