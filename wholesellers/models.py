from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


class WholeSeller(models.Model):
    user_id = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
    )
    region = models.CharField(max_length=100)
    points_earned = models.IntegerField()
    points_redeemed = models.IntegerField(default=0)
    current_points = models.IntegerField(default=0)

    REQUIRED_FIELDS = ["region", "points_earned"]

    def __str__(self) -> str:
        return f"wholeseller: {self.user_id}"

    class Meta:
        db_table = "wholesellers"
