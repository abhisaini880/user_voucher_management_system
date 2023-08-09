from rest_framework import serializers
from cart.models import Order, Transaction, Points, VoucherAPITokens
from datetime import datetime
from users.serializers import UserSerializer


status_mapping = {0: "Order Placed", 1: "Delivered", 2: "Reedemed"}


class OrderSerializer(serializers.ModelSerializer):
    def update(self, instance, validated_data):
        instance.status = validated_data["status"]
        instance.message = validated_data["message"]
        instance.save()

        return instance

    def to_representation(self, data):
        data = super(OrderSerializer, self).to_representation(data)
        data["status"] = status_mapping[data["status"]]
        data["created_at"] = datetime.fromisoformat(
            data["created_at"]
        ).strftime("%Y-%m-%d %H:%M:%S")
        return data

    class Meta:
        model = Order
        fields = "__all__"


class TransactionSerializer(serializers.ModelSerializer):
    def update(self, instance, validated_data):
        instance.voucher_code = validated_data["voucher_code"]
        instance.save()

        return instance

    class Meta:
        model = Transaction
        fields = "__all__"


class TransactionReportSerializer(serializers.ModelSerializer):
    user_id = UserSerializer(read_only=True)

    def to_representation(self, data):
        data = super(TransactionReportSerializer, self).to_representation(data)
        data["created_at"] = datetime.fromisoformat(
            data["created_at"]
        ).strftime("%Y-%m-%d %H:%M:%S")
        data["name"] = data["user_id"]["name"]
        data["mobile_number"] = data["user_id"]["mobile_number"]
        data["user_id"] = data["user_id"]["id"]

        return data

    class Meta:
        model = Transaction
        fields = "__all__"
        extra_fields = ["user_id"]


class PointSerializer(serializers.ModelSerializer):
    def to_representation(self, data):
        data = super(PointSerializer, self).to_representation(data)
        data["created_at"] = datetime.fromisoformat(
            data["created_at"]
        ).strftime("%Y-%m-%d %H:%M:%S")

        return data

    class Meta:
        model = Points
        fields = "__all__"


class TokenSerializer(serializers.ModelSerializer):
    def update(self, instance, validated_data):
        instance.token = validated_data["token"]
        instance.save()

        return instance

    class Meta:
        model = VoucherAPITokens
        fields = "__all__"
