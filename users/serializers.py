from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate

User = get_user_model()

# User Serializer
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "name", "mobile_number")


# Register Serializer
class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "name", "mobile_number", "password")
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            validated_data["name"],
            validated_data["mobile_number"],
            validated_data["password"],
        )

        return user


# Login Serializer
class LoginSerializer(serializers.Serializer):
    mobile_number = serializers.IntegerField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(**data)
        if user and user.is_active:
            return user
        raise serializers.ValidationError("Incorrect Credentials")
