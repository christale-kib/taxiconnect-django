from django.db import models


class TaxiEnrollment(models.Model):
    """
    Traçage des enrôlements taxi-à-taxi.
    Un chauffeur (parrain) enrôle un autre chauffeur (recrue).
    """
    parrain_chauffeur_id = models.IntegerField(help_text="ID du chauffeur parrain (MySQL)")
    recrue_chauffeur_id = models.IntegerField(help_text="ID du chauffeur recruté (MySQL)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("parrain_chauffeur_id", "recrue_chauffeur_id")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Taxi {self.parrain_chauffeur_id} → {self.recrue_chauffeur_id}"
