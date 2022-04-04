from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate

User = get_user_model()

# User Serializer
class UserSerializer(serializers.ModelSerializer):
    def update(self, instance, validated_data):
        instance.name = validated_data["name"]
        instance.region = validated_data["region"]
        instance.points_earned = validated_data["points_earned"]
        instance.points_redeemed = validated_data["points_redeemed"]
        instance.current_points = validated_data["current_points"]
        instance.is_active = validated_data["is_active"]
        instance.save()

        return instance

    def create(self, validated_data):
        user = User.objects.create_user(
            name=validated_data["name"],
            mobile_number=validated_data["mobile_number"],
            password=validated_data["password"],
            region=validated_data["region"],
            points_earned=validated_data["points_earned"],
        )

        return user

    class Meta:
        model = User
        fields = (
            "id",
            "name",
            "mobile_number",
            "region",
            "staff",
            "is_active",
            "current_points",
            "points_earned",
            "password",
            "points_redeemed",
        )
        extra_kwargs = {
            "password": {"write_only": True},
        }


# # Register Serializer
# class RegisterSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ("id", "name", "mobile_number")
#         extra_kwargs = {"password": {"write_only": True}}

#     def create(self, validated_data):
#         user = User.objects.create_user(
#             name=validated_data["name"],
#             mobile_number=validated_data["mobile_number"],
#             password=validated_data["password"],
#             region=validated_data["region"],
#             points_earned=validated_data["points_earned"],
#         )

#         return user


# Login Serializer
class LoginSerializer(serializers.Serializer):
    mobile_number = serializers.IntegerField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(**data)
        if user and user.is_active:
            return user
        raise serializers.ValidationError("Incorrect Credentials")
