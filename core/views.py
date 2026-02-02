from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect
from django.utils import timezone
from .models import BAProfile
from .models_legacy import BrandAmbassadors
from .services import (
    get_dashboard_payload, get_challenges, get_leaderboard, get_recent_recruits, get_stations,
    create_driver_enrollment, create_passenger_enrollment, get_zones
)



def login_page(request):
    if request.user.is_authenticated:
        return redirect("ba_app")
    mode = request.GET.get("mode", "login")  # login | register
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "login":
            email = (request.POST.get("email") or "").strip().lower()
            password = request.POST.get("password") or ""
            user = authenticate(request, username=email, password=password)
            if user:
                login(request, user)
                return redirect("ba_app")
            messages.error(request, "Email ou mot de passe incorrect")
        elif action == "register":
            from django.contrib.auth.models import User
            nom = (request.POST.get("nom") or "").strip()
            prenom = (request.POST.get("prenom") or "").strip()
            telephone = (request.POST.get("telephone") or "").strip()
            email = (request.POST.get("email") or "").strip().lower()
            password = request.POST.get("password") or ""
            if User.objects.filter(username=email).exists():
                messages.error(request, "Cet email existe déjà.")
            else:
                # 1) Créer user Django
                u = User.objects.create_user(
                    username=email,
                    email=email,
                    password=password,
                    first_name=prenom,
                    last_name=nom,
                )
                # 2) Créer profile BA Django (UI / objectifs)
                BAProfile.objects.create(
                    user=u,
                    telephone=telephone,
                    monthly_target=100,
                    level="Brand Ambassador"
                )
                # 3) Créer (ou récupérer) le BA MySQL
                # ⚠️ email + telephone sont uniques côté MySQL
                BrandAmbassadors.objects.get_or_create(
                    email=email,
                    defaults={
                        "nom": nom,
                        "prenom": prenom,
                        "telephone": telephone or f"TEMP-{u.id}",
                        "password_hash": "",  # tu peux mettre un vrai hash plus tard
                        "niveau": "Brand Ambassador",
                        "statut": "ACTIF",
                        "created_at": timezone.now(),
                        "updated_at": timezone.now(),
                    }
                )
                # 4) Login
                login(request, u)
                return redirect("ba_app")
    return render(request, "core/login.html", {"mode": mode})


def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def ba_app(request):
    tab = request.GET.get("tab", "dashboard")
    ctx = {
        "tab": tab,
        "ba": get_dashboard_payload(request.user),
        "challenges": get_challenges(request.user),
        "leaderboard": get_leaderboard(),
        "recruits": get_recent_recruits(request.user),
        "zones": get_zones(),
    }
    return render(request, "core/app.html", ctx)


@login_required
@transaction.atomic
def enroll_driver(request):
    if request.method != "POST":
        return redirect("ba_app")
    try:
        create_driver_enrollment(request.user, request.POST)
        messages.success(request, "✅ Enrôlement chauffeur réussi !")
    except Exception as e:
        messages.error(request, f"❌ Échec enrôlement chauffeur: {str(e)}")
    return redirect("/app/?tab=dashboard")


@login_required
@transaction.atomic
def enroll_passenger(request):
    if request.method != "POST":
        return redirect("ba_app")
    try:
        create_passenger_enrollment(request.user, request.POST)
        messages.success(request, "✅ Enrôlement passager réussi !")
    except Exception as e:
        messages.error(request, f"❌ Échec enrôlement passager: {str(e)}")
    return redirect("/app/?tab=dashboard")