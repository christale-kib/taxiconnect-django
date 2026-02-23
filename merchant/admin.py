from django.contrib import admin
from .models import Merchant


@admin.register(Merchant)
class MerchantAdmin(admin.ModelAdmin):
    list_display = ("prenom", "nom", "nom_commerce", "numero_merchant", "telephone", "ba_email", "statut", "created_at")
    list_filter = ("statut", "created_at")
    search_fields = ("nom", "prenom", "nom_commerce", "numero_merchant", "telephone", "ba_email")
    readonly_fields = ("created_at", "updated_at")
