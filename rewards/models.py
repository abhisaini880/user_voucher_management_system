from django.db import models


class Reward(models.Model):
    reward_id = models.AutoField(primary_key=True)
    product_code = models.CharField(max_length=120, blank=True)
    brand = models.CharField(max_length=100, null=False)
    brand_heading = models.CharField(max_length=255, null=True, blank=True)
    brand_value = models.IntegerField(null=False)
    points_value = models.IntegerField(null=False)
    expiry = models.IntegerField(null=True)
    brand_image = models.URLField(null=False)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Reward: {self.reward_id}"

    class Meta:
        db_table = "rewards"
