import pandas as pd
from django.core.files.base import ContentFile

from rest_framework import generics, permissions, viewsets
from rest_framework.response import Response
from knox.models import AuthToken

from django.contrib.auth import get_user_model
from rest_framework.decorators import action
from rest_framework import status
from .serializers import UserSerializer, LoginSerializer
import utils


User = get_user_model()


class PingAPI(generics.GenericAPIView):
    def get(self, request):
        return Response({"success": True}, status=status.HTTP_200_OK)


class LoginAPI(generics.GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request):
        mobile_number = request.data.get("mobile_number")
        if not User.objects.filter(mobile_number=mobile_number).exists():
            return Response(
                "User Doesn't exists", status=status.HTTP_400_BAD_REQUEST
            )

        user = User.objects.get(mobile_number=mobile_number)
        otp = utils.generate_otp()
        user.otp = otp
        user.login_retry = 0
        user.save()
        # utils.send_otp(mobile_number, otp)
        return Response(
            "OTP Sent to mobile number !", status=status.HTTP_200_OK
        )

    def put(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data
        _, token = AuthToken.objects.create(user)
        return Response(
            {
                "user": UserSerializer(
                    user, context=self.get_serializer_context()
                ).data,
                "token": token,
            }
        )


class UserViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    permission_map = {
        "list": [permissions.IsAuthenticated, permissions.IsAdminUser],
        "retrieve": [permissions.IsAuthenticated],
        "create": [
            permissions.IsAuthenticated,
            permissions.IsAdminUser,
        ],
        "update": [
            permissions.IsAuthenticated,
            permissions.IsAdminUser,
        ],
        "bulk_create": [
            permissions.IsAuthenticated,
            permissions.IsAdminUser,
        ],
        "bulk_update": [
            permissions.IsAuthenticated,
            permissions.IsAdminUser,
        ],
    }

    def list(self, request):
        queryset = User.objects.all()
        serializer = UserSerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk):
        queryset = User.objects.filter(id=pk)
        serializer = UserSerializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            # Make entry in points table
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk):
        request_data = request.data
        try:
            user_data = User.objects.get(id=pk)
        except:
            return Response(
                "User doesn't exist !",
                status=status.HTTP_400_BAD_REQUEST,
            )
        updated_data = {
            "name": request_data.get("name") or user_data.name,
            "region": request_data.get("region") or user_data.region,
            "points_earned": request_data.get("points_earned")
            or user_data.points_earned,
            "points_redeemed": request_data.get("points_redeemed")
            or user_data.points_redeemed,
            "is_active": request_data.get("is_active") or user_data.is_active,
        }

        updated_data["current_points"] = (
            updated_data["points_earned"] - updated_data["points_redeemed"]
        )

        if updated_data["current_points"] < 0:
            return Response(
                "Can't update the points value below its redeemed value.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = UserSerializer(user_data, data=updated_data, partial=True)
        if serializer.is_valid():
            serializer.save()
            # Make entry in points table
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=["post"], detail=False)
    def bulk_create(self, request):
        file = request.FILES["users"]

        content = file.read()  # these are bytes
        file_content = ContentFile(content)

        user_df = pd.read_csv(file_content)

        required_headers = [
            "mobile_number",
            "password",
            "name",
            "region",
            "points_earned",
        ]

        if user_df.empty:
            return Response(
                "Received Empty File ! Please try again.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not all(header in user_df.columns for header in required_headers):
            return Response(
                "File Missing Required Fields !",
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_data_list = user_df.to_dict("records")
        incorrect_user_list = []
        for index, data in enumerate(user_data_list):
            serializer = UserSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                # Make entry in points table
            else:
                incorrect_user_list.append([index, serializer.errors])

        if incorrect_user_list:
            return Response(incorrect_user_list)
        return Response("Successfully registered users !")

    @action(methods=["put"], detail=False)
    def bulk_update(self, request):
        file = request.FILES["users"]

        content = file.read()  # these are bytes
        file_content = ContentFile(content)

        user_df = pd.read_csv(file_content)

        required_headers = [
            "mobile_number",
            "name",
            "region",
            "points_earned",
        ]

        if user_df.empty:
            return Response(
                "Received Empty File ! Please try again.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not all(header in user_df.columns for header in required_headers):
            return Response(
                "File Missing Required Fields !",
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_data_list = user_df.to_dict("records")
        incorrect_user_list = []
        for index, data in enumerate(user_data_list):

            try:
                user_data = User.objects.get(
                    mobile_number=data["mobile_number"]
                )
            except:
                incorrect_user_list.append([index, "User Doesn't exists"])
                continue

            updated_data = {
                "name": data.get("name") or user_data.name,
                "region": data.get("region") or user_data.region,
                "points_earned": data.get("points_earned")
                or user_data.points_earned,
                "points_redeemed": data.get("points_redeemed")
                or user_data.points_redeemed,
                "is_active": data.get("is_active") or user_data.is_active,
            }

            updated_data["current_points"] = (
                updated_data["points_earned"] - updated_data["points_redeemed"]
            )

            if updated_data["current_points"] < 0:
                incorrect_user_list.append(
                    {
                        index: "Can't update the points value below its redeemed value."
                    }
                )
                continue
            serializer = UserSerializer(
                user_data, data=updated_data, partial=True
            )
            if serializer.is_valid():
                serializer.save()
                # Make entry in points table
            else:
                incorrect_user_list.append({index: serializer.errors})

        if incorrect_user_list:
            return Response(incorrect_user_list)
        return Response("Successfully updated users !")

    def get_permissions(self):
        try:
            return [
                permission() for permission in self.permission_map[self.action]
            ]
        except KeyError:
            return [permission() for permission in self.permission_classes]
