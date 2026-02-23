from django.db import models
from django.contrib.auth.models import User


class Merchant(models.Model):
    """Marchand recruté par un BA."""
    STATUT_CHOICES = [
        ("INSCRIT", "Inscrit"),
        ("ACTIF", "Actif"),
        ("SUSPENDU", "Suspendu"),
        ("REJETÉ", "Rejeté"),
    ]

    ba_email = models.CharField(
        max_length=255,
        help_text="Email du BA recruteur (lien avec MySQL brand_ambassadors)",
    )
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    telephone = models.CharField(max_length=30, unique=True)
    adresse = models.CharField(max_length=255, blank=True, default="")
    numero_merchant = models.CharField(
        max_length=50, unique=True,
        help_text="Numéro marchand Airtel Money",
    )
    nom_commerce = models.CharField(max_length=200)

    # Photos stockées en base64 (data:image/…;base64,…)
    photo_id_recto = models.TextField(blank=True, default="", help_text="Pièce d'identité - recto (base64)")
    photo_id_verso = models.TextField(blank=True, default="", help_text="Pièce d'identité - verso (base64)")
    photo_rccm = models.TextField(blank=True, default="", help_text="Document de commerce RCCM (base64)")

    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="INSCRIT")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Marchand"
        verbose_name_plural = "Marchands"

    def __str__(self):
        return f"{self.prenom} {self.nom} - {self.nom_commerce} ({self.numero_merchant})"
