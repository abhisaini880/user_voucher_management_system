from cart.models import Order, Transaction, Points
from django.contrib.auth import get_user_model
from rest_framework import viewsets, permissions
from cart.serializers import (
    OrderSerializer,
    TransactionSerializer,
    PointSerializer,
)
from rest_framework.response import Response
from rest_framework import status
import utils

User = get_user_model()
status_mapping = {"Placed": 0, "Completed": 1, "Failed": 2}


class OrderViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrderSerializer

    permission_map = {
        "list": [permissions.IsAuthenticated, permissions.IsAdminUser],
        "retrieve": [permissions.IsAuthenticated],
        "create": [
            permissions.IsAuthenticated,
        ],
        "update": [
            permissions.IsAuthenticated,
            permissions.IsAdminUser,
        ],
    }

    def get_permissions(self):
        try:
            return [
                permission() for permission in self.permission_map[self.action]
            ]
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
        # create order id
        request_data["order_id"] = utils.unique_order_id_generator(Order)

        if request_data["status"] not in status_mapping.keys():
            return Response(
                "Invalid Status",
                status=status.HTTP_400_BAD_REQUEST,
            )

        request_data["status"] = status_mapping[
            request_data.get("status", "Placed")
        ]
        request_data["user_id"] = user.id

        order_serializer = OrderSerializer(data=request_data)
        if not order_serializer.is_valid():
            return Response(
                order_serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

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
                "brand_value": data.get("brand_value"),
                "points_value": data.get("points_value"),
                "quantity": data.get("quantity"),
            }

            transaction_data["points_reedemed"] = (
                transaction_data["points_value"] * transaction_data["quantity"]
            )

            transaction_seralizer = TransactionSerializer(
                data=transaction_data
            )
            if not transaction_seralizer.is_valid():
                incorrect_transaction_list.append(
                    [index, transaction_seralizer.errors]
                )
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
            "message": f"Placed Order - #{request_data['order_id']}",
            "balance": user.current_points,
        }

        point_serializer = PointSerializer(data=points_data)
        if point_serializer.is_valid(raise_exception=True):
            point_serializer.save()

        if incorrect_transaction_list:
            return Response(
                incorrect_transaction_list, status=status.HTTP_400_BAD_REQUEST
            )

        return Response(order_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, pk):
        request_data = request.data
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

        previous_order_status = Order_data.status
        updated_data = {
            "status": status_mapping[request_data.get("status", "Placed")],
            "message": request_data["message"],
        }
        serializer = OrderSerializer(
            Order_data, data=updated_data, partial=True
        )
        if serializer.is_valid():
            serializer.save()

            # If order status is failed then return points to user
            user = Order_data.user_id
            if (
                request_data.get("status")
                and updated_data["status"] == 2
                and previous_order_status != 2
            ):
                user.points_earned += Order_data.total_points_value
                user.current_points = user.points_earned - user.points_redeemed
                user.save()

                # Make Entry in Points table
                points_data = {
                    "user_id": user.id,
                    "points_earned": Order_data.total_points_value,
                    "message": request_data.get("message"),
                    "balance": user.current_points,
                }

                point_serializer = PointSerializer(data=points_data)
                if point_serializer.is_valid(raise_exception=True):
                    point_serializer.save()

            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TransactionViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TransactionSerializer

    permission_map = {
        "list": [permissions.IsAuthenticated, permissions.IsAdminUser],
        "retrieve": [permissions.IsAuthenticated],
    }

    def get_permissions(self):
        try:
            return [
                permission() for permission in self.permission_map[self.action]
            ]
        except KeyError:
            return [permission() for permission in self.permission_classes]

    def list(self, request):
        queryset = Transaction.objects.all()
        serializer = TransactionSerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk, **kwargs):
        queryset = Transaction.objects.filter(order_id=pk)
        serializer = TransactionSerializer(queryset, many=True)
        return Response(serializer.data)


class PointViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PointSerializer

    permission_map = {
        "list": [permissions.IsAuthenticated, permissions.IsAdminUser],
        "retrieve": [permissions.IsAuthenticated],
    }

    def get_permissions(self):
        try:
            return [
                permission() for permission in self.permission_map[self.action]
            ]
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
