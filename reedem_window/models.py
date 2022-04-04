from django.db import models


class RedeemWindow(models.Model):
    window_id = models.AutoField(primary_key=True)
    open_at = models.DateTimeField()
    close_at = models.DateTimeField()
    is_active = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"Window: {self.window_id}"

    class Meta:
        db_table = "reedem_window"
