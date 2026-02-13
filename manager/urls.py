from django.urls import path
from . import views

urlpatterns = [
    path("", views.manager_login, name="manager_login"),
    path("dashboard/", views.manager_dashboard, name="manager_dashboard"),
    path("logout/", views.manager_logout, name="manager_logout"),
    path("api/data/", views.api_dashboard_data, name="manager_api_data"),
    path("api/config/", views.update_config, name="manager_api_config"),
]
