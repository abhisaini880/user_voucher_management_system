from datetime import datetime
from reedem_window.models import RedeemWindow
from rest_framework import viewsets, permissions
from reedem_window.serializers import WindowSerializer
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status
from users.api import IsAdminView, IsEditor


class WindowViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = WindowSerializer

    permission_map = {
        "list": [permissions.IsAuthenticated, IsAdminView, IsEditor],
        "active_window": [permissions.IsAuthenticated],
        "create": [permissions.IsAuthenticated, IsEditor],
        "update": [permissions.IsAuthenticated, IsEditor],
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
        window = (
            RedeemWindow.objects.filter(is_active=True)
            .filter(open_at__lt=datetime.now())
            .filter(close_at__gt=datetime.now())
        )
        window_status = window.exists()
        serializer = WindowSerializer(window, many=True)
        return Response(
            {"Window_active": window_status, "data": serializer.data}
        )

    def create(self, request):
        start_date = request.data.get("start_date")
        end_date = request.data.get("end_date")

        if RedeemWindow.objects.filter(is_active=True).exists():
            window = RedeemWindow.objects.get(is_active=True)
            window.is_active = False
            window.save()

        try:
            data = {
                "open_at": datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S"),
                "close_at": datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S"),
                "is_active": True,
            }
        except:
            return Response("Date format should be `YYYY-MM-DD HH:MM:SS`")

        serializer = WindowSerializer(data=data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request):
        end_date = request.data.get("end_date")
        if RedeemWindow.objects.filter(is_active=True).exists():
            window = RedeemWindow.objects.filter(is_active=True).first()
            try:
                data = {
                    "close_at": datetime.strptime(
                        end_date, "%Y-%m-%d %H:%M:%S"
                    ),
                }
            except:
                return Response("Date format should be `YYYY-MM-DD HH:MM:SS`")
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
