from datetime import datetime
from reedem_window.models import RedeemWindow
from rest_framework import viewsets, permissions
from reedem_window.serializers import WindowSerializer
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status


class WindowViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = WindowSerializer

    permission_map = {
        "list": [permissions.IsAuthenticated, permissions.IsAdminUser],
        "active_window": [permissions.IsAuthenticated],
        "create": [permissions.IsAuthenticated, permissions.IsAdminUser],
        "update": [
            permissions.IsAuthenticated,
            permissions.IsAdminUser,
        ],
    }

    def get_permissions(self):
        try:
            return [
                permission() for permission in self.permission_map[self.action]
            ]
        except KeyError:
            return [permission() for permission in self.permission_classes]

    def list(self, request):
        queryset = RedeemWindow.objects.all()
        serializer = WindowSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=["get"], detail=False)
    def active_window(self, request):
        window_status = RedeemWindow.objects.filter(is_active=True).exists()
        return Response(
            {
                "Window_active": window_status,
            }
        )

    def create(self, request):
        if RedeemWindow.objects.filter(is_active=True).exists():
            return Response(
                {"message": "Window already active"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = {
            "open_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "is_active": True,
        }

        serializer = WindowSerializer(data=data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request):
        if RedeemWindow.objects.filter(is_active=True).exists():
            window = RedeemWindow.objects.filter(is_active=True).first()
            data = {
                "close_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "is_active": False,
            }
            serializer = WindowSerializer(window, data=data, partial=True)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return Response(
                    serializer.data, status=status.HTTP_202_ACCEPTED
                )

        return Response(
            {"message": "No Window is active"},
            status=status.HTTP_400_BAD_REQUEST,
        )
