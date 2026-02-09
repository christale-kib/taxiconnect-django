from django.urls import path
from . import views

urlpatterns = [
    path("", views.login_page, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("app/", views.ba_app, name="ba_app"),
    path("app/enroll/driver/", views.enroll_driver, name="enroll_driver"),
    path("app/enroll/passenger/", views.enroll_passenger, name="enroll_passenger"),
    path("app/withdraw/", views.withdraw_commission, name="withdraw_commission"),
]
