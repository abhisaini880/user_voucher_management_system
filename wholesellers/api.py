import pandas as pd


from django.core.files.base import ContentFile

from wholesellers.models import WholeSeller
from django.contrib.auth import get_user_model
from rest_framework import viewsets, permissions
from wholesellers.serializers import WholeSellerSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from users.serializers import RegisterSerializer

User = get_user_model()


class WholeSellerViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = WholeSellerSerializer

    permission_map = {
        "create": [
            permissions.IsAuthenticated,
            permissions.IsAdminUser,
        ],
        "list": [
            permissions.IsAuthenticated,
        ],
        "bulk_create": [
            permissions.IsAuthenticated,
            permissions.IsAdminUser,
        ],
        "update": [
            permissions.IsAuthenticated,
            permissions.IsAdminUser,
        ],
    }

    def list(self, request):
        user = request.user
        queryset = WholeSeller.objects.filter(user_id=user)
        serializer = WholeSellerSerializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        request_data = self.create_user_if_not_present(request.data)
        serializer = WholeSellerSerializer(data=request_data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk):
        request_data = request.data
        try:
            wholeseller_data = WholeSeller.objects.get(user_id=pk)
        except:
            return Response(
                "WholeSeller doesn't exist !",
                status=status.HTTP_400_BAD_REQUEST,
            )

        updated_data = {
            "region": request_data["region"]
            if request_data.get("region")
            else wholeseller_data.region,
            "points_earned": request_data["points_earned"]
            if request_data.get("points_earned")
            else wholeseller_data.points_earned,
        }
        serializer = WholeSellerSerializer(
            wholeseller_data, data=updated_data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=["post"],
        detail=False,
        url_path="bulk",
        url_name="bulk_wholesellers",
    )
    def bulk_create(self, request):
        file = request.FILES["wholesellers"]

        content = file.read()  # these are bytes
        file_content = ContentFile(content)

        wholeseller_df = pd.read_csv(file_content)

        required_headers = [
            "mobile_number",
            "password",
            "name",
            "region",
            "points_earned",
        ]

        if wholeseller_df.empty:
            return Response(
                "Received Empty File ! Please try again.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not all(
            header in wholeseller_df.columns for header in required_headers
        ):
            return Response(
                "File Missing Required Fields !",
                status=status.HTTP_400_BAD_REQUEST,
            )

        wholeseller_data_list = wholeseller_df.to_dict("records")
        incorrect_wholeseller_list = []
        for index, data in enumerate(wholeseller_data_list):
            wholeseller_data = self.create_user_if_not_present(data)
            serializer = WholeSellerSerializer(data=wholeseller_data)
            if serializer.is_valid():
                serializer.save()
            else:
                incorrect_wholeseller_list.append({index: serializer.errors})

        return Response("Successfully upload the data")

    def create_user_if_not_present(self, request_data):
        mobile_number = request_data.get("mobile_number")

        user_data = User.objects.filter(mobile_number=mobile_number)
        user_data = list(user_data.values())
        if not user_data:
            user_data = {
                "mobile_number": mobile_number,
                "name": request_data.get("name"),
                "password": request_data.get("password"),
            }
            user_serializer = RegisterSerializer(data=user_data)
            user_serializer.is_valid(raise_exception=True)
            user = user_serializer.save()
            request_data["user_id"] = user.id
        else:
            request_data["user_id"] = user_data[0].get("id")

        return request_data

    def get_permissions(self):
        try:
            return [
                permission() for permission in self.permission_map[self.action]
            ]
        except KeyError:
            return [permission() for permission in self.permission_classes]
