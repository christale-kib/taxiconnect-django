from django.db import models
from django.contrib.auth.models import User


class ManagerProfile(models.Model):
    """Profil Manager lié à un User Django."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="manager_profile")
    role = models.CharField(max_length=50, default="manager")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Manager: {self.user.username}"


class ObjectiveConfig(models.Model):
    """Configuration des objectifs BA et chauffeurs — singleton."""
    # BA objectives
    ba_recruits_target = models.IntegerField(default=12)
    ba_activation_target = models.IntegerField(default=60, help_text="% minimum")
    ba_min_passengers = models.IntegerField(default=10)
    ba_commission_per_recruit = models.IntegerField(default=5000)
    ba_bonus_streak3 = models.IntegerField(default=3000)
    ba_bonus_streak7 = models.IntegerField(default=8000)
    ba_bonus_top = models.IntegerField(default=15000)
    ba_period = models.CharField(max_length=20, default="mensuel")

    # Driver objectives
    drv_min_trips_week = models.IntegerField(default=15)
    drv_min_rating = models.DecimalField(max_digits=3, decimal_places=1, default=4.0)
    drv_max_cancel_rate = models.IntegerField(default=10, help_text="%")
    drv_min_ontime_rate = models.IntegerField(default=85, help_text="%")
    drv_min_passengers_week = models.IntegerField(default=5)
    drv_bonus_active = models.IntegerField(default=2000)
    drv_period = models.CharField(max_length=20, default="hebdomadaire")

    # Tiers (stored as JSON)
    tiers_json = models.JSONField(default=list, blank=True, help_text="Liste des paliers commission")

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuration Objectifs"
        verbose_name_plural = "Configuration Objectifs"

    def __str__(self):
        return "Config Objectifs"

    @classmethod
    def get_config(cls):
        obj, _ = cls.objects.get_or_create(pk=1, defaults={
            "tiers_json": [
                {"name": "Bronze", "minRecruits": 1, "maxRecruits": 4, "commission": 5000, "color": "#CD7F32"},
                {"name": "Argent", "minRecruits": 5, "maxRecruits": 9, "commission": 6000, "color": "#C0C0C0"},
                {"name": "Or", "minRecruits": 10, "maxRecruits": 14, "commission": 7500, "color": "#FFD700"},
                {"name": "Diamant", "minRecruits": 15, "maxRecruits": 999, "commission": 10000, "color": "#00BCD4"},
            ]
        })
        return obj
