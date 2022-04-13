from rest_framework import serializers
from reedem_window.models import RedeemWindow
from datetime import datetime


class WindowSerializer(serializers.ModelSerializer):
    def to_representation(self, data):
        data = super(WindowSerializer, self).to_representation(data)
        data["open_at"] = datetime.fromisoformat(data["open_at"]).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        data["close_at"] = datetime.fromisoformat(data["close_at"]).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        return data

    class Meta:
        model = RedeemWindow
        fields = "__all__"
