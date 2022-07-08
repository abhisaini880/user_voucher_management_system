import pandas as pd
from django.core.files.base import ContentFile

from rest_framework import generics, permissions, viewsets
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from django.http import JsonResponse
from knox.models import AuthToken

from django.contrib.auth import get_user_model
from cart.serializers import PointSerializer
from rest_framework.decorators import action
from rest_framework import status
from .serializers import UserSerializer, LoginSerializer
import utils


User = get_user_model()


class PingAPI(generics.GenericAPIView):
    def get(self, request):
        return Response({"success": True}, status=status.HTTP_200_OK)


class IsEditor(BasePermission):
    def has_permission(self, request, view):
        return request.user.staff_editor


class IsAdminView(BasePermission):
    def has_permission(self, request, view):
        return request.user.staff


class LoginAPI(generics.GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request):
        mobile_number = request.data.get("mobile_number")
        if not User.objects.filter(mobile_number=mobile_number).exists():
            return Response(
                {"success": False, "messgae": "User Doesn't Exists !"}
            )

        user = User.objects.get(mobile_number=mobile_number)
        otp = utils.generate_otp()
        user.otp = otp
        user.login_retry = 0
        user.save()
        message, template_id = utils.generate_message(key="otp", value=otp)
        utils.send_sms(
            mobile=mobile_number, message=message, template_id=template_id
        )
        return JsonResponse(
            {"success": True, "messgae": "OTP Sent to mobile number !"},
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
        "list": [permissions.IsAuthenticated, IsEditor, IsAdminView],
        "retrieve": [permissions.IsAuthenticated],
        "create": [
            permissions.IsAuthenticated,
            IsEditor,
        ],
        "update": [
            permissions.IsAuthenticated,
            IsEditor,
        ],
        "bulk_create": [
            permissions.IsAuthenticated,
            IsEditor,
        ],
        "bulk_update": [
            permissions.IsAuthenticated,
            IsEditor,
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
        mobile_number = request.data.get("mobile_number")
        if not mobile_number or len(str(mobile_number)) != 10:
            return Response("Invalid mobile number")

        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            user_data = serializer.data
            user_id = user_data.get("id")
            user = User.objects.get(id=user_id)
            # Make Entry in Points table
            user.current_points = user.points_earned
            user.save()

            points_data = {
                "user_id": user_id,
                "points_earned": user.points_earned,
                "message": "Points Credited to Your Account",
                "balance": user.current_points,
            }

            point_serializer = PointSerializer(data=points_data)
            if point_serializer.is_valid(raise_exception=True):
                point_serializer.save()

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
            "ws_name": request_data.get("ws_name") or user_data.ws_name,
            "region": request_data.get("region") or user_data.region,
            "is_active": request_data.get("is_active", user_data.is_active),
            "points_earned": user_data.points_earned
            + request_data.get("add_points", 0),
            "points_redeemed": user_data.points_redeemed
            + request_data.get("delete_points", 0),
        }

        updated_data["current_points"] = (
            updated_data["points_earned"] - updated_data["points_redeemed"]
        )

        if updated_data["current_points"] < 0:
            return Response(
                "Can't update the points value below 0.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        diff = updated_data["current_points"] - user_data.current_points

        serializer = UserSerializer(user_data, data=updated_data, partial=True)
        if serializer.is_valid():
            serializer.save()
            # Make entry in points table
            points_data = {
                "user_id": user_data.id,
                "message": request_data.get("message"),
                "points_earned": 0,
                "points_reedemed": 0,
            }

            if diff > 0:
                points_data["points_earned"] = diff
            elif diff < 0:
                points_data["points_reedemed"] = abs(diff)

            points_data["balance"] = user_data.current_points

            point_serializer = PointSerializer(data=points_data)
            if point_serializer.is_valid(raise_exception=True):
                point_serializer.save()

            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        request_data = request.data
        user_ids = request_data.get("user_ids")

        if User.objects.filter(id__in=user_ids).exists():
            count = User.objects.filter(id__in=user_ids).delete()
            print(count)
            return Response(
                {"message": f"{count[0]} User were deleted successfully!"},
                status=status.HTTP_204_NO_CONTENT,
            )

    @action(methods=["post"], detail=False)
    def bulk_create(self, request):
        file = request.FILES["users"]

        content = file.read()  # these are bytes
        file_content = ContentFile(content)

        try:
            user_df = pd.read_csv(file_content)
        except Exception as err:
            return Response(
                {
                    "success": False,
                    "message": "Invalid CSV File.",
                    "debug_message": str(err),
                }
            )

        required_headers = [
            "mobile_number",
            "unique_id",
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

            if (
                not data.get("mobile_number")
                or len(str(data.get("mobile_number"))) != 10
            ):
                incorrect_user_list.append(
                    [index + 2, {"mobile_number": ["Invalid mobile number !"]}]
                )
                continue

            serializer = UserSerializer(data=data)
            if serializer.is_valid():
                serializer.save()

                user_data = serializer.data
                user_id = user_data.get("id")
                user = User.objects.get(id=user_id)
                # Make Entry in Points table
                user.current_points = user.points_earned
                user.save()

                points_data = {
                    "user_id": user_id,
                    "points_earned": user.points_earned,
                    "message": "Points Credited to Your Account",
                    "balance": user.current_points,
                }

                point_serializer = PointSerializer(data=points_data)
                if point_serializer.is_valid(raise_exception=True):
                    point_serializer.save()

            else:
                incorrect_user_list.append([index + 2, serializer.errors])

        if incorrect_user_list:
            return Response({"success": False, "data": incorrect_user_list})
        return Response(
            {"success": True, "message": "Successfully registered users !"}
        )

    @action(methods=["put"], detail=False)
    def bulk_update(self, request):
        file = request.FILES["users"]

        content = file.read()  # these are bytes
        file_content = ContentFile(content)

        try:
            user_df = pd.read_csv(file_content)
        except Exception as err:
            return Response(
                {
                    "success": False,
                    "message": "Invalid CSV File.",
                    "debug_message": str(err),
                }
            )

        required_headers = [
            "mobile_number",
            "name",
            "region",
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
                incorrect_user_list.append(
                    [
                        index + 2,
                        {
                            "mobile_number": [
                                "User with mobile number Doesn't exists"
                            ]
                        },
                    ]
                )
                continue

            updated_data = {
                "name": data.get("name") or user_data.name,
                "ws_name": data.get("ws_name") or user_data.ws_name,
                "region": data.get("region") or user_data.region,
                "is_active": data.get("is_active", user_data.is_active),
                "points_earned": user_data.points_earned
                + data.get("add_points", 0),
                "points_redeemed": user_data.points_redeemed
                + data.get("delete_points", 0),
            }

            updated_data["current_points"] = (
                updated_data["points_earned"] - updated_data["points_redeemed"]
            )

            if updated_data["current_points"] < 0:
                return Response(
                    "Can't update the points value below 0.",
                    status=status.HTTP_400_BAD_REQUEST,
                )

            diff = updated_data["current_points"] - user_data.current_points

            if updated_data["current_points"] < 0:
                incorrect_user_list.append(
                    {
                        index
                        + 2: {
                            "points_earned": [
                                "Can't update the points value below 0."
                            ]
                        }
                    }
                )
                continue
            serializer = UserSerializer(
                user_data, data=updated_data, partial=True
            )
            if serializer.is_valid():
                serializer.save()

                # Make entry in points table
                points_data = {
                    "user_id": user_data.id,
                    "message": data.get("message"),
                }

                if diff > 0:
                    points_data["points_earned"] = diff
                    points_data["points_reedemed"] = 0
                elif diff < 0:
                    points_data["points_earned"] = 0
                    points_data["points_reedemed"] = abs(diff)

                points_data["balance"] = user_data.current_points

                point_serializer = PointSerializer(data=points_data)
                if point_serializer.is_valid(raise_exception=True):
                    point_serializer.save()
            else:
                incorrect_user_list.append({index + 2: serializer.errors})

        if incorrect_user_list:
            return Response({"success": False, "data": incorrect_user_list})
        return Response(
            {"success": True, "message": "Successfully updated users !"}
        )

    def get_permissions(self):
        try:
            return [
                permission() for permission in self.permission_map[self.action]
            ]
        except KeyError:
            return [permission() for permission in self.permission_classes]
