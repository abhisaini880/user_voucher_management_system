from rest_framework import serializers
from reedem_window.models import RedeemWindow


class WindowSerializer(serializers.ModelSerializer):
    def update(self, instance, validated_data):
        instance.close_at = validated_data["close_at"]
        instance.is_active = validated_data["is_active"]
        instance.save()

        return instance

    class Meta:
        model = RedeemWindow
        fields = "__all__"
