from django.urls import path
from . import views

urlpatterns = [
    path("", views.taxi_login_page, name="taxi_login"),
    path("logout/", views.taxi_logout_view, name="taxi_logout"),
    path("app/", views.taxi_app, name="taxi_app"),
    path("app/enroll/taxi/", views.taxi_enroll, name="taxi_enroll"),
    path("app/payment/", views.taxi_payment, name="taxi_payment"),
]
