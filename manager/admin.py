from django.contrib import admin
from .models import ManagerProfile, ObjectiveConfig


@admin.register(ManagerProfile)
class ManagerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "created_at")


@admin.register(ObjectiveConfig)
class ObjectiveConfigAdmin(admin.ModelAdmin):
    list_display = ("__str__", "ba_recruits_target", "drv_min_trips_week", "updated_at")
