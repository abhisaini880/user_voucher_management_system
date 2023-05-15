from xml.dom import ValidationErr
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate

User = get_user_model()

# User Serializer
class UserSerializer(serializers.ModelSerializer):
    def update(self, instance, validated_data):
        instance.name = validated_data["name"]
        instance.ws_name = validated_data["ws_name"]
        instance.region = validated_data["region"]
        instance.points_earned = validated_data["points_earned"]
        instance.points_redeemed = validated_data["points_redeemed"]
        instance.current_points = validated_data["current_points"]
        instance.read_only = validated_data["read_only"]
        instance.voucher_write = validated_data["voucher_write"]
        instance.upi_id = validated_data.get("upi_id")
        instance.save()

        return instance

    def create(self, validated_data):
        user = User.objects.create_user(
            name=validated_data["name"],
            ws_name=validated_data["ws_name"],
            unique_id=validated_data["unique_id"],
            mobile_number=validated_data["mobile_number"],
            region=validated_data["region"],
            upi_id=validated_data.get("upi_id"),
            points_earned=validated_data["points_earned"],
        )

        return user

    class Meta:
        model = User
        fields = (
            "id",
            "name",
            "ws_name",
            "mobile_number",
            "unique_id",
            "region",
            "upi_id",
            "staff",
            "is_active",
            "current_points",
            "points_earned",
            "otp",
            "points_redeemed",
            "staff_editor",
            "read_only",
            "voucher_write",
        )
        extra_kwargs = {
            "otp": {"write_only": True},
        }


# Login Serializer
class LoginSerializer(serializers.Serializer):
    mobile_number = serializers.IntegerField()
    otp = serializers.CharField()

    def validate(self, data):
        if not User.objects.filter(
            mobile_number=data["mobile_number"]
        ).exists():
            raise serializers.ValidationError("User Doesn't exists !")

        user = User.objects.get(mobile_number=data["mobile_number"])

        if user.login_retry > 3:
            raise serializers.ValidationError("OTP Expired !")
        elif user.otp == data["otp"]:
            user.login_retry = 5
            user.save()
            return user

        user.login_retry += 1
        user.save()
        raise serializers.ValidationError("Invalid OTP !")
