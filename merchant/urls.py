from django.urls import path
from . import views

urlpatterns = [
    path("", views.merchant_login, name="merchant_login"),
    path("logout/", views.merchant_logout, name="merchant_logout"),
    path("app/", views.merchant_app, name="merchant_app"),
    path("app/enroll/", views.enroll_merchant, name="enroll_merchant"),
    path("api/merchant/<int:merchant_id>/", views.merchant_detail_api, name="merchant_detail_api"),
    # Nouvelles URLs — Merchant Manager Dashboard
    path("dashboard/", views.merchant_dashboard, name="merchant_dashboard"),
    path("api/merchant/<int:merchant_id>/status/", views.update_merchant_status, name="merchant_status_api"),
]