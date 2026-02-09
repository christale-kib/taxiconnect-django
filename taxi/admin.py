from django.contrib import admin
from .models import TaxiEnrollment

@admin.register(TaxiEnrollment)
class TaxiEnrollmentAdmin(admin.ModelAdmin):
    list_display = ("parrain_chauffeur_id", "recrue_chauffeur_id", "created_at")
    list_filter = ("created_at",)
