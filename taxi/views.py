from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect
from django.utils import timezone
from core.models import TaxiProfile
from core.models_legacy import Chauffeurs
from core.services import get_zones
from .services import (
    get_taxi_dashboard, get_taxi_leaderboard, get_taxi_recent_recruits,
    get_taxi_recent_payments, create_taxi_enrollment, create_payment,
)


def taxi_login_page(request):
    if request.user.is_authenticated and hasattr(request.user, "taxi_profile"):
        return redirect("taxi_app")
    mode = request.GET.get("mode", "login")
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "login":
            email = (request.POST.get("email") or "").strip().lower()
            password = request.POST.get("password") or ""
            user = authenticate(request, username=email, password=password)
            if user:
                if not hasattr(user, "taxi_profile"):
                    messages.error(request, "Ce compte n'est pas un compte chauffeur.")
                else:
                    login(request, user)
                    return redirect("taxi_app")
            else:
                messages.error(request, "Email ou mot de passe incorrect")
        elif action == "register":
            from django.contrib.auth.models import User
            nom = (request.POST.get("nom") or "").strip()
            prenom = (request.POST.get("prenom") or "").strip()
            telephone = (request.POST.get("telephone") or "").strip()
            email = (request.POST.get("email") or "").strip().lower()
            password = request.POST.get("password") or ""
            immatriculation = (request.POST.get("immatriculation") or "").strip().upper()
            vehicle_model = (request.POST.get("vehicleModel") or "N/A").strip()
            zone = (request.POST.get("zone") or "").strip()

            if User.objects.filter(username=email).exists():
                messages.error(request, "Cet email existe déjà.")
            elif not telephone:
                messages.error(request, "Téléphone obligatoire.")
            elif not immatriculation:
                messages.error(request, "Immatriculation obligatoire.")
            else:
                try:
                    from core.services import get_or_create_station_for_zone, normalize_and_validate_immatriculation
                    vehicle_number = normalize_and_validate_immatriculation(immatriculation)
                    station = get_or_create_station_for_zone(zone) if zone else None

                    # 1) User Django
                    u = User.objects.create_user(
                        username=email, email=email, password=password,
                        first_name=prenom, last_name=nom,
                    )
                    # 2) Chauffeur MySQL
                    marque = vehicle_model.split(" ")[0] if vehicle_model != "N/A" else "N/A"
                    ch = Chauffeurs.objects.create(
                        ba_id=1,  # BA par défaut (admin) — à ajuster
                        station_id=station.id if station else None,
                        nom=nom,
                        prenom=prenom,
                        telephone=telephone,
                        email=email,
                        vehicule_immatriculation=vehicle_number,
                        vehicule_marque=marque,
                        vehicule_modele=vehicle_model,
                        vehicule_couleur="N/A",
                        photo_profil_url="temp.jpg",
                        photo_id_url="temp_id.jpg",
                        statut="ACTIF",
                        created_at=timezone.now(),
                        updated_at=timezone.now(),
                    )
                    # 3) TaxiProfile
                    TaxiProfile.objects.create(
                        user=u,
                        telephone=telephone,
                        chauffeur_id=ch.id,
                    )
                    login(request, u)
                    return redirect("taxi_app")
                except Exception as e:
                    messages.error(request, f"Erreur inscription: {str(e)}")

    return render(request, "taxi/login.html", {"mode": mode, "zones": get_zones()})


def taxi_logout_view(request):
    logout(request)
    return redirect("taxi_login")


@login_required
def taxi_app(request):
    if not hasattr(request.user, "taxi_profile"):
        return redirect("taxi_login")
    tab = request.GET.get("tab", "dashboard")
    try:
        dashboard = get_taxi_dashboard(request.user)
    except ValueError:
        messages.error(request, "Profil chauffeur introuvable.")
        return redirect("taxi_login")

    ctx = {
        "tab": tab,
        "driver": dashboard,
        "leaderboard": get_taxi_leaderboard(),
        "recruits": get_taxi_recent_recruits(request.user),
        "payments": get_taxi_recent_payments(request.user),
        "zones": get_zones(),
    }
    return render(request, "taxi/app.html", ctx)


@login_required
@transaction.atomic
def taxi_enroll(request):
    """Chauffeur enrôle un autre taxi."""
    if request.method != "POST":
        return redirect("taxi_app")
    try:
        create_taxi_enrollment(request.user, request.POST)
        messages.success(request, "✅ Taxi enrôlé avec succès !")
    except Exception as e:
        messages.error(request, f"❌ Échec enrôlement taxi: {str(e)}")
    return redirect("/taxi/app/?tab=dashboard")


@login_required
@transaction.atomic
def taxi_payment(request):
    """Chauffeur initie un paiement pour un passager."""
    if request.method != "POST":
        return redirect("taxi_app")
    try:
        tx, ref = create_payment(request.user, request.POST)
        messages.success(request, f"✅ Paiement initié ! Réf: {ref} — {tx.montant} XAF")
    except Exception as e:
        messages.error(request, f"❌ Échec paiement: {str(e)}")
    return redirect("/taxi/app/?tab=payments")
