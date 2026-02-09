from django.contrib import admin
from .models import BAProfile, TaxiProfile, RetraitCommission

@admin.register(BAProfile)
class BAProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "telephone", "level", "monthly_target")

@admin.register(TaxiProfile)
class TaxiProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "telephone", "chauffeur_id")

@admin.register(RetraitCommission)
class RetraitCommissionAdmin(admin.ModelAdmin):
    list_display = ("ba_email", "montant", "statut", "telephone_retrait", "created_at")
    list_filter = ("statut",)
