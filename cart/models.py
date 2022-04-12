from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

STATUS = [(0, "Placed"), (1, "Delivered"), (2, "Reedemed")]


class Order(models.Model):
    order_id = models.CharField(max_length=120, blank=True)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    total_brand_value = models.IntegerField(null=False)
    total_points_value = models.IntegerField(null=False)
    status = models.IntegerField(choices=STATUS, default=0)
    message = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    REQUIRED_FIELDS = [
        "order_id",
        "user_id",
        "total_brand_value",
        "total_points_value",
        "status",
    ]

    def __str__(self) -> str:
        return f"Order: {self.order_id}"

    class Meta:
        db_table = "orders"


class Transaction(models.Model):
    transaction_id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    order_id = models.CharField(max_length=120, blank=True)
    brand = models.CharField(max_length=100, null=False)
    brand_value = models.IntegerField(null=False)
    points_value = models.IntegerField(null=False)
    quantity = models.IntegerField(null=False, default=1)
    points_reedemed = models.IntegerField(null=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Transaction: {self.transaction_id}"

    class Meta:
        db_table = "transactions"


class Points(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    points_earned = models.IntegerField(null=False, default=0)
    points_reedemed = models.IntegerField(null=False, default=0)
    balance = models.IntegerField(null=False)
    message = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Points: {self.user_id} - {self.balance}"

    class Meta:
        db_table = "points"
