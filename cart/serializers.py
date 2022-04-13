from rest_framework import serializers
from cart.models import Order, Transaction, Points

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
        return data

    class Meta:
        model = Order
        fields = "__all__"


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = "__all__"


class PointSerializer(serializers.ModelSerializer):
    class Meta:
        model = Points
        fields = "__all__"
