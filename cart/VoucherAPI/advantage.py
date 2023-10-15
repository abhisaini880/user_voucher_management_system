from django.conf import settings
import requests
from json import dumps
from cart.models import VoucherAPITokens

from cart.serializers import TokenSerializer

api_tokens = settings.ADVANTAGE_API_TOKENS


class AdvantageAPI:
    def __init__(self):
        self.token_data = VoucherAPITokens.objects.get(brand="Advantage")
        self.grant_type = api_tokens.get("grant_type")
        self.code = api_tokens.get("code")
        self.client_id = api_tokens.get("client_id")
        self.client_secret = api_tokens.get("client_secret")
        self.redirect_uri = api_tokens.get("redirect_uri")
        self.auth_token = self.token_data.token
        self.error = None

    def generate_auth_token(self):
        """
        Generate the Auth token using Advantage API if existing token is expired
        """

        try:
            url = "https://secure.workadvantage.in/oauth/token"
            params = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": self.grant_type,
                "redirect_uri": self.redirect_uri,
                "code": self.code,
            }

            response = requests.post(url=url, params=params)
            if response.status_code == 200:
                response = response.json()
                self.auth_token = response.get("access_token")
                updated_data = {"token": self.auth_token}
                serializer = TokenSerializer(
                    self.token_data, data=updated_data, partial=True
                )
                if serializer.is_valid():
                    serializer.save()

                    return None

            else:
                self.error = f"Received status code - {response.status_code}"

        except Exception as error:
            print(f"Error in generating Advantage API Token")
            print(str(error))
            self.error = "Error in generating Advantage API Token"

    def list_catalog(self):
        voucher_list = []
        try:
            url = "https://secure.workadvantage.in/api/v1/catalogs"

            headers = {"Authorization": self.auth_token}

            params = {"iso3_code": "IND", "page": "0", "limit": 100}

            response = requests.get(url=url, headers=headers, params=params)
            if response.status_code == 401 or (
                response.status_code == 200
                and response.json().get("info")
                == "You don't have access to this api"
            ):
                # Auth token is expired, regenerate it
                self.generate_auth_token()
                headers["Authorization"] = self.auth_token
                response = requests.get(
                    url=url, headers=headers, params=params
                )

            if response.status_code == 200:
                response = response.json()

                if response.get("success") == True:
                    deals = response.get("dealList")
                    for deal in deals:
                        product_info = {
                            "name": deal.get("name"),
                            "logo": deal.get("images", {}).get("logo"),
                        }
                        benefits = deal.get("benefits")
                        for benefit in benefits:
                            benefit.update(product_info)
                        voucher_list.extend(benefits)

                    return voucher_list

                else:
                    self.error = response.get("info")

            else:
                self.error = f"Received status code - {response.status_code}"

        except Exception as error:
            print(f"Error in generating Advantage API Token")
            print(str(error))
            self.error = "Error in generating Advantage API Token"
            return voucher_list

    def place_order(self, order_id: str, order_details: dict):
        """
        Place order for vouchers

        Args:
            order_id (str): Order id
            order_details (dict): order data
        """
        voucher_list = []
        try:

            url = "https://secure.workadvantage.in/external_order_place"

            headers = {"Authorization": self.auth_token}

            params = {
                "type": "Web",
                "quantity": order_details.get("quantity"),
                "billing_name": "Abhishek",
                "billing_email": "abhisaini880@gmail.com",
                "contact": order_details.get("user_contact"),
                "postal_code": "122001",
                "city": "Gurgaon",
                "address_line1": "Dlf City",
                "state": "Haryana",
                "country": "India",
                "reference_id": order_id,
                "upc_id": order_details.get("upc_id"),
                "receiver_email": order_details.get("user_email"),
            }

            response = requests.post(url=url, headers=headers, params=params)
            if response.status_code == 401:
                # Auth token is expired, regenerate it
                self.generate_auth_token()
                headers["Authorization"] = self.auth_token
                response = requests.get(
                    url=url, headers=headers, params=params
                )

            if response.status_code == 200:
                response = response.json()
                if response.get("success") == True:
                    resp_data = response.get("result", {})

                    if not resp_data.get("success"):
                        self.error = resp_data.get("message")

                    else:
                        for voucher in resp_data.get("codes"):
                            voucher_list.append(
                                (
                                    voucher.get("cardnumber"),
                                    voucher.get("pin_or_url"),
                                )
                            )

                    return voucher_list

                else:
                    self.error = response.get("info")

            else:
                self.error = f"Received status code - {response.status_code}"

            return voucher_list

        except Exception as error:
            print(f"Error in generating Advantage API Token")
            print(str(error))
            self.error = "Error in generating Advantage API Token"
            return voucher_list
