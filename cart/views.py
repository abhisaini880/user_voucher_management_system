import pandas as pd
from django.core.files.base import ContentFile

from cart.models import Order, Transaction, Points
from rewards.models import Reward
from django.contrib.auth import get_user_model
from rest_framework import viewsets, permissions
from cart.serializers import (
    OrderSerializer,
    TransactionSerializer,
    TransactionReportSerializer,
    PointSerializer,
)
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status
import utils
from users.api import IsAdminView, IsEditor
from cart.VoucherAPI.muthoot import MuthootAPI
from cart.VoucherAPI.advantage import AdvantageAPI

User = get_user_model()
status_mapping = {"Order Placed": 0, "Delivered": 1, "Reedemed": 3}
Muthoot_api = MuthootAPI()
Advantage_api = AdvantageAPI()


class OrderViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrderSerializer

    permission_map = {
        "list": [permissions.IsAuthenticated, IsAdminView],
        "retrieve": [permissions.IsAuthenticated],
        "create": [
            permissions.IsAuthenticated,
        ],
        "update": [permissions.IsAuthenticated, IsEditor],
    }

    def get_permissions(self):
        try:
            return [permission() for permission in self.permission_map[self.action]]
        except KeyError:
            return [permission() for permission in self.permission_classes]

    def list(self, request):
        queryset = Order.objects.all()
        serializer = OrderSerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk):
        queryset = Order.objects.filter(user_id=pk)
        serializer = OrderSerializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        request_data = request.data
        user = request.user

        # check if user is inactive return with error
        if user.read_only:
            return Response(
                "Can't execute order, user is inactive !",
                status=status.HTTP_400_BAD_REQUEST,
            )

        # create order id
        request_data["order_id"] = utils.unique_order_id_generator(Order)

        if request_data["status"] not in status_mapping.keys():
            return Response(
                "Invalid Status",
                status=status.HTTP_400_BAD_REQUEST,
            )

        request_data["status"] = status_mapping[
            request_data.get("status", "Order Placed")
        ]
        request_data["user_id"] = user.id

        order_serializer = OrderSerializer(data=request_data)
        if not order_serializer.is_valid():
            return Response(order_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # check if user has enough points
        if user.current_points < request_data.get("total_points_value"):
            return Response(
                "Can't execute order, not enough points in wallet !",
                status=status.HTTP_400_BAD_REQUEST,
            )
        order_serializer.save()

        # Make Transactions
        incorrect_transaction_list = []
        for index, data in enumerate(request_data.get("vouchers_data", [])):
            transaction_data = {
                "user_id": request_data.get("user_id"),
                "order_id": request_data["order_id"],
                "brand": data.get("brand"),
                "brand_heading": data.get("brand_heading"),
                "brand_value": data.get("brand_value"),
                "points_value": data.get("points_value"),
                "quantity": data.get("quantity"),
            }

            transaction_data["points_reedemed"] = (
                transaction_data["points_value"] * transaction_data["quantity"]
            )

            # Generate vocher code if branch is Muthoot
            if transaction_data.get("brand", "").lower() == "muthoot":
                reward = Reward.objects.get(product_code=data.get("product_code"))

                if not reward:
                    return Response(
                        "Reward doesn't exist !",
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                voucher_details = [
                    {
                        "ProductCode": data.get("product_code"),
                        "Quantity": data.get("quantity"),
                        "VoucherAmt": data.get("brand_value"),
                        "DueDays": reward.expiry if reward.expiry else 90,
                    }
                ]

                Muthoot_order_id = f"{request_data.get('order_id', 'ORD')}_{index}"
                order_value = data.get("brand_value") * data.get("quantity")
                voucher_codes = Muthoot_api.place_order(
                    order_id=Muthoot_order_id,
                    order_value=order_value,
                    order_details=voucher_details,
                )
                transaction_data["voucher_code"] = ",".join(voucher_codes)

                # Send sms to customer
                for code in voucher_codes:
                    message, template_id = utils.generate_message(
                        "muthoot_order",
                        (
                            data.get("brand_heading"),
                            code,
                        ),
                    )
                    utils.send_sms(
                        mobile=user.mobile_number,
                        message=message,
                        template_id=template_id,
                    )

            else:
                Advantage_order_id = f"{request_data.get('order_id', 'ORD')}_{index}"

                voucher_details = {
                    "upc_id": data.get("product_code"),
                    "quantity": data.get("quantity"),
                    "user_contact": user.mobile_number,
                    "user_email": user.email_id,
                }

                voucher_codes = Advantage_api.place_order(
                    order_id=Advantage_order_id,
                    order_details=voucher_details,
                )

                # voucher_codes : [(code, pin)]
                codes = []
                for code in voucher_codes:
                    temp_code = code[0]
                    if code[1]:
                        temp_code += f"({code[1]})"
                    codes.append(temp_code)

                transaction_data["voucher_code"] = ",".join(codes)

                for code in codes:
                    message, template_id = utils.generate_message(
                        "muthoot_order",
                        (
                            data.get("brand_heading"),
                            code,
                        ),
                    )
                    utils.send_sms(
                        mobile=user.mobile_number,
                        message=message,
                        template_id=template_id,
                    )

            transaction_seralizer = TransactionSerializer(data=transaction_data)
            if not transaction_seralizer.is_valid():
                incorrect_transaction_list.append([index, transaction_seralizer.errors])
                continue

            transaction_seralizer.save()

        # deduct user points
        user.points_redeemed += request_data.get("total_points_value")
        user.current_points = user.points_earned - user.points_redeemed
        user.save()

        # Make Entry in Points table
        points_data = {
            "user_id": user.id,
            "points_reedemed": request_data.get("total_points_value"),
            "message": f"Points Debited for Order ID #{request_data['order_id']}",
            "balance": user.current_points,
        }

        point_serializer = PointSerializer(data=points_data)
        if point_serializer.is_valid(raise_exception=True):
            point_serializer.save()

        if incorrect_transaction_list:
            return Response(
                incorrect_transaction_list, status=status.HTTP_400_BAD_REQUEST
            )

        message, template_id = utils.generate_message("order", request_data["order_id"])
        utils.send_sms(
            mobile=user.mobile_number, message=message, template_id=template_id
        )

        return Response(order_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, pk):
        request_data = request.data
        user = request.user
        # check if user is inactive return with error
        if user.read_only:
            return Response(
                "Can't execute order, user is inactive !",
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            Order_data = Order.objects.get(order_id=pk)
        except:
            return Response(
                "Order doesn't exist !",
                status=status.HTTP_400_BAD_REQUEST,
            )

        if request_data["status"] not in status_mapping.keys():
            return Response(
                "Invalid Status",
                status=status.HTTP_400_BAD_REQUEST,
            )

        updated_data = {
            "status": status_mapping[request_data.get("status", "Order Placed")],
            "message": request_data["message"],
        }
        serializer = OrderSerializer(Order_data, data=updated_data, partial=True)
        if serializer.is_valid():
            serializer.save()

            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=["put"], detail=False)
    def bulk_update(self, request):
        file = request.FILES["orders"]
        user = request.user
        # check if user is inactive return with error
        if user.read_only:
            return Response(
                "Can't execute order, user is inactive !",
                status=status.HTTP_400_BAD_REQUEST,
            )

        content = file.read()  # these are bytes
        file_content = ContentFile(content)

        try:
            order_df = pd.read_csv(file_content)
        except Exception as err:
            return Response(
                {
                    "success": False,
                    "message": "Invalid CSV File.",
                    "debug_message": str(err),
                }
            )

        required_headers = ["order_id", "status"]

        if order_df.empty:
            return Response(
                "Received Empty File ! Please try again.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not all(header in order_df.columns for header in required_headers):
            return Response(
                "File Missing Required Fields !",
                status=status.HTTP_400_BAD_REQUEST,
            )

        order_data_list = order_df.to_dict("records")
        incorrect_order_list = []
        for index, data in enumerate(order_data_list):
            try:
                order_data = Order.objects.get(order_id=data["order_id"])
            except:
                incorrect_order_list.append(
                    [
                        index + 2,
                        {"order_id": ["order Doesn't exists"]},
                    ]
                )
                continue

            updated_data = {"status": data.get("status")}

            serializer = OrderSerializer(order_data, data=updated_data, partial=True)
            if serializer.is_valid():
                serializer.save()
            else:
                incorrect_order_list.append({index + 2: serializer.errors})

        if incorrect_order_list:
            return Response({"success": False, "data": incorrect_order_list})
        return Response({"success": True, "message": "Successfully updated orders !"})


class TransactionViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TransactionReportSerializer

    permission_map = {
        "list": [IsAdminView],
        "retrieve": [permissions.IsAuthenticated],
        "bulk_update": [IsAdminView],
    }

    def get_permissions(self):
        try:
            return [permission() for permission in self.permission_map[self.action]]
        except KeyError:
            return [permission() for permission in self.permission_classes]

    def list(self, request):
        queryset = Transaction.objects.all()
        serializer = TransactionReportSerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk, **kwargs):
        queryset = Transaction.objects.filter(order_id=pk)
        serializer = TransactionReportSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=["put"], detail=False)
    def bulk_update(self, request):
        file = request.FILES["voucher"]

        content = file.read()  # these are bytes
        file_content = ContentFile(content)

        try:
            voucher_df = pd.read_csv(file_content)
        except Exception as err:
            return Response(
                {
                    "success": False,
                    "message": "Invalid CSV File.",
                    "debug_message": str(err),
                }
            )

        required_headers = ["transaction_id", "voucher_code"]

        if voucher_df.empty:
            return Response(
                "Received Empty File ! Please try again.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not all(header in voucher_df.columns for header in required_headers):
            return Response(
                "File Missing Required Fields !",
                status=status.HTTP_400_BAD_REQUEST,
            )

        voucher_data_list = voucher_df.to_dict("records")
        incorrect_transaction_list = []
        for index, data in enumerate(voucher_data_list):
            try:
                transaction_data = Transaction.objects.get(
                    transaction_id=data["transaction_id"]
                )
            except:
                incorrect_transaction_list.append(
                    [
                        index + 2,
                        {"transaction_id": ["transaction Doesn't exists"]},
                    ]
                )
                continue

            # If transcation belongs to Muthoot brand then skip it.
            if transaction_data.brand.lower() == "muthoot":
                continue

            updated_data = {"voucher_code": data.get("voucher_code")}

            serializer = TransactionSerializer(
                transaction_data, data=updated_data, partial=True
            )
            if serializer.is_valid():
                serializer.save()
            else:
                incorrect_transaction_list.append({index + 2: serializer.errors})

        if incorrect_transaction_list:
            return Response({"success": False, "data": incorrect_transaction_list})
        return Response({"success": True, "message": "Successfully updated vouchers !"})


class PointViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PointSerializer

    permission_map = {
        "list": [permissions.IsAuthenticated, IsAdminView],
        "retrieve": [permissions.IsAuthenticated],
    }

    def get_permissions(self):
        try:
            return [permission() for permission in self.permission_map[self.action]]
        except KeyError:
            return [permission() for permission in self.permission_classes]

    def list(self, request):
        queryset = Points.objects.all()
        serializer = PointSerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk, **kwargs):
        queryset = Points.objects.filter(user_id=pk)
        serializer = PointSerializer(queryset, many=True)
        return Response(serializer.data)
