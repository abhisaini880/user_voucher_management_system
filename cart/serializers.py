from rest_framework import serializers
from cart.models import Order, Voucher, Transaction

status_mapping = {0: "Placed", 1: "Completed", 2: "Failed"}


class OrderSerializer(serializers.ModelSerializer):
    def update(self, instance, validated_data):
        instance.status = validated_data["status"]
        instance.message = validated_data["message"]
        instance.save()

        return instance

    def to_representation(self, data):
        data = super(OrderSerializer, self).to_representation(data)
        data["status"] = status_mapping[data["status"]]
        return data

    class Meta:
        model = Order
        fields = "__all__"


class VoucherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Voucher
        fields = "__all__"


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = "__all__"
