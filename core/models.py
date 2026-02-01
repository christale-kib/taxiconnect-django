
from django.db import models
from django.contrib.auth.models import User


class BAProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="ba_profile")
    telephone = models.CharField(max_length=30, blank=True, default="")
    monthly_target = models.PositiveIntegerField(default=100)
    level = models.CharField(max_length=50, default="Brand Ambassador")
    def __str__(self):
        return f"{self.user.username} profile"