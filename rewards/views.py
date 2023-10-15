import pandas as pd
from django.core.files.base import ContentFile

from rest_framework import permissions, viewsets
from rest_framework.response import Response

from django.contrib.auth import get_user_model
from rest_framework.decorators import action
from rest_framework import status

from rewards.models import Reward
from cart.VoucherAPI.advantage import AdvantageAPI
from .serializers import RewardSerializer
from users.api import IsAdminView, IsEditor
import utils


User = get_user_model()
Advantage_api = AdvantageAPI()


class RewardViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RewardSerializer

    permission_map = {
        "list": [permissions.IsAuthenticated],
        "create": [permissions.IsAuthenticated, IsEditor],
        "update": [permissions.IsAuthenticated, IsEditor],
        "bulk_create": [permissions.IsAuthenticated, IsEditor],
        "bulk_update": [permissions.IsAuthenticated, IsEditor],
        "delete": [permissions.IsAuthenticated, IsEditor],
    }

    def list(self, request):
        request_data = request.GET

        if request_data.get("status", "").lower() == "true":
            queryset = Reward.objects.filter(status=True)
        else:
            queryset = Reward.objects.all()
        serializer = RewardSerializer(queryset, many=True)

        reward_data_list = [dict(entry) for entry in serializer.data]
        rewards = {
            "rewards": reward_data_list,
        }

        custom_rewards = Advantage_api.list_catalog()

        if not Advantage_api.error:
            rewards["custom_rewards"] = custom_rewards

        return Response(rewards)

    def create(self, request):
        request_data = request.data

        if not request_data:
            return Response(
                "Invalid Request !", status=status.HTTP_400_BAD_REQUEST
            )

        reward_data = {
            "product_code": utils.unique_product_code_generator(Reward),
            "brand": request_data.get("brand"),
            "brand_heading": request_data.get("brand_heading"),
            "brand_value": request_data.get("brand_value"),
            "points_value": request_data.get("points_value"),
            "brand_image": request_data.get("brand_image"),
        }

        # Add expiry if `Muthoot` brand
        if reward_data.get("brand", "").lower() == "muthoot":
            reward_data["expiry"] = 90

        serializer = RewardSerializer(data=reward_data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk):
        request_data = request.data
        try:
            reward_data = Reward.objects.get(reward_id=pk)
        except:
            return Response(
                "Reward doesn't exist !",
                status=status.HTTP_400_BAD_REQUEST,
            )
        updated_data = {
            "brand": request_data.get("brand") or reward_data.brand,
            "brand_value": request_data.get("brand_value")
            or reward_data.brand_value,
            "brand_heading": request_data.get("brand_heading")
            or reward_data.brand_heading,
            "points_value": request_data.get("points_value")
            or reward_data.points_value,
            "brand_image": request_data.get("brand_image")
            or reward_data.brand_image,
            "status": request_data.get("status", reward_data.status),
        }

        serializer = RewardSerializer(
            reward_data, data=updated_data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        request_data = request.data
        reward_ids = request_data.get("reward_ids")

        if Reward.objects.filter(reward_id__in=reward_ids).exists():
            count = Reward.objects.filter(reward_id__in=reward_ids).delete()
            return Response(
                {"message": f"{count[0]} Rewards were deleted successfully!"},
                status=status.HTTP_200_OK,
            )

    @action(methods=["post"], detail=False)
    def bulk_create(self, request):
        file = request.FILES["users"]

        content = file.read()  # these are bytes
        file_content = ContentFile(content)

        try:
            rewards_df = pd.read_csv(file_content)
        except Exception as err:
            return Response(
                {
                    "success": False,
                    "message": "Invalid CSV File.",
                    "debug_message": str(err),
                }
            )

        required_headers = [
            "brand",
            "brand_heading",
            "brand_value",
            "points_value",
            "brand_image",
        ]

        if rewards_df.empty:
            return Response(
                "Received Empty File ! Please try again.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not all(
            header in rewards_df.columns for header in required_headers
        ):
            return Response(
                "File Missing Required Fields !",
                status=status.HTTP_400_BAD_REQUEST,
            )

        reward_data_list = rewards_df.to_dict("records")
        incorrect_reward_list = []
        for index, data in enumerate(reward_data_list):
            data["product_code"] = utils.unique_product_code_generator(Reward)
            # Add expiry if `Muthoot` brand
            if data.get("brand", "").lower() == "muthoot":
                data["expiry"] = 90
            serializer = RewardSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
            else:
                incorrect_reward_list.append([index, serializer.errors])

        if incorrect_reward_list:
            return Response(incorrect_reward_list)
        return Response("Successfully added rewards !")

    # @action(methods=["put"], detail=False)
    # def bulk_update(self, request):
    #     file = request.FILES["users"]

    #     content = file.read()  # these are bytes
    #     file_content = ContentFile(content)

    #     rewards_df = pd.read_csv(file_content)

    #     required_headers = [
    #         "brand",
    #         "brand_heading",
    #         "brand_value",
    #         "points_value",
    #         "brand_image",
    #     ]

    #     if rewards_df.empty:
    #         return Response(
    #             "Received Empty File ! Please try again.",
    #             status=status.HTTP_400_BAD_REQUEST,
    #         )

    #     if not all(
    #         header in rewards_df.columns for header in required_headers
    #     ):
    #         return Response(
    #             "File Missing Required Fields !",
    #             status=status.HTTP_400_BAD_REQUEST,
    #         )

    #     reward_data_list = rewards_df.to_dict("records")
    #     incorrect_reward_list = []
    #     for index, data in enumerate(reward_data_list):

    #         try:
    #             reward_data = Reward.objects.get(
    #                 mobile_number=data["mobile_number"]
    #             )
    #         except:
    #             incorrect_reward_list.append([index, "Reward Doesn't exists"])
    #             continue

    #         updated_data = {
    #             "name": data.get("name") or user_data.name,
    #             "region": data.get("region") or user_data.region,
    #             "points_earned": data.get("points_earned")
    #             or user_data.points_earned,
    #             "points_redeemed": data.get("points_redeemed")
    #             or user_data.points_redeemed,
    #             "is_active": data.get("is_active") or user_data.is_active,
    #         }

    #         updated_data["current_points"] = (
    #             updated_data["points_earned"] - updated_data["points_redeemed"]
    #         )

    #         if updated_data["current_points"] < 0:
    #             incorrect_user_list.append(
    #                 {
    #                     index: "Can't update the points value below its redeemed value."
    #                 }
    #             )
    #             continue
    #         serializer = UserSerializer(
    #             user_data, data=updated_data, partial=True
    #         )
    #         if serializer.is_valid():
    #             serializer.save()
    #             # Make entry in points table
    #         else:
    #             incorrect_user_list.append({index: serializer.errors})

    #     if incorrect_user_list:
    #         return Response(incorrect_user_list)
    #     return Response("Successfully updated users !")

    def get_permissions(self):
        try:
            return [
                permission() for permission in self.permission_map[self.action]
            ]
        except KeyError:
            return [permission() for permission in self.permission_classes]
