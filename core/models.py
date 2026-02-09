from django.db import models
from django.contrib.auth.models import User


class BAProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="ba_profile")
    telephone = models.CharField(max_length=30, blank=True, default="")
    monthly_target = models.PositiveIntegerField(default=100)
    level = models.CharField(max_length=50, default="Brand Ambassador")

    def __str__(self):
        return f"{self.user.username} profile"


class TaxiProfile(models.Model):
    """Profil Django pour les chauffeurs (app Taxi)."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="taxi_profile")
    telephone = models.CharField(max_length=30, blank=True, default="")
    chauffeur_id = models.IntegerField(null=True, blank=True, help_text="FK vers chauffeurs MySQL")

    def __str__(self):
        return f"Taxi: {self.user.username}"


class RetraitCommission(models.Model):
    """Demande de retrait de commission par un BA."""
    STATUT_CHOICES = [
        ("PENDING", "En attente"),
        ("EN_COURS", "En cours"),
        ("PAYÉ", "Payé"),
        ("REJETÉ", "Rejeté"),
    ]
    ba_email = models.CharField(max_length=255, help_text="Email du BA (lien avec MySQL)")
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    telephone_retrait = models.CharField(max_length=30)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="PENDING")
    reference = models.CharField(max_length=100, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Retrait {self.montant} XAF - {self.ba_email} - {self.statut}"
