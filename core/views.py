import json
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect
from django.utils import timezone
from .models import BAProfile
from .models_legacy import BrandAmbassadors
from .services import (
    get_dashboard_payload, get_challenges, get_leaderboard, get_recent_recruits,
    get_stations, create_driver_enrollment, create_passenger_enrollment,
    get_zones, get_withdrawals, create_withdrawal,
)


def login_page(request):
    if request.user.is_authenticated:
        return redirect("ba_app")
    mode = request.GET.get("mode", "login")
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
                u = User.objects.create_user(
                    username=email, email=email, password=password,
                    first_name=prenom, last_name=nom,
                )
                BAProfile.objects.create(
                    user=u, telephone=telephone,
                    monthly_target=100, level="Brand Ambassador",
                )
                BrandAmbassadors.objects.get_or_create(
                    email=email,
                    defaults={
                        "nom": nom, "prenom": prenom,
                        "telephone": telephone or f"TEMP-{u.id}",
                        "password_hash": "", "niveau": "Brand Ambassador",
                        "statut": "ACTIF",
                        "created_at": timezone.now(), "updated_at": timezone.now(),
                    },
                )
                login(request, u)
                return redirect("ba_app")
    return render(request, "core/login.html", {"mode": mode})


def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def ba_app(request):
    tab = request.GET.get("tab", "dashboard")
    ba = get_dashboard_payload(request.user)
    recruits = get_recent_recruits(request.user)
    leaderboard = get_leaderboard()
    withdrawals = get_withdrawals(request.user)
    zones = get_zones()

    # Build rankings JSON for the new design
    ba_name = ba["name"]
    rankings_json = []
    for item in leaderboard:
        rankings_json.append({
            "name": item["name"],
            "recruits": item["total_enrollments"],
            "score": item["total_enrollments"] * 5000,
            "isYou": item["name"].strip().lower() == ba_name.strip().lower(),
        })

    # Build recruits JSON
    recruits_json = []
    for r in recruits:
        status_map = {"Activé": "actif", "Inscrit": "en_attente"}
        recruits_json.append({
            "id": r["id"],
            "name": r["name"],
            "type": r["type"],
            "phone": "",
            "city": "",
            "plate": "",
            "vehicle": r["type"],
            "airtel": "",
            "status": status_map.get(r["status"], "en_attente"),
            "date": r["date"],
            "passengers": 0,
            "commission": r["commission"],
            "notes": "",
        })

    # Build transactions JSON from withdrawals
    transactions_json = []
    for i, w in enumerate(withdrawals):
        transactions_json.append({
            "id": i + 1,
            "type": "debit",
            "label": f"Retrait - {w['reference']}",
            "amount": -w["montant"],
            "date": w["date"],
            "status": w["statut"],
        })

    ctx = {
        "tab": tab,
        "ba": ba,
        "challenges": get_challenges(request.user),
        "leaderboard": leaderboard,
        "recruits": recruits,
        "zones": zones,
        "withdrawals": withdrawals,
        # JSON data for the new JS-driven design
        "ba_json": json.dumps(ba),
        "recruits_json": json.dumps(recruits_json),
        "rankings_json": json.dumps(rankings_json),
        "transactions_json": json.dumps(transactions_json),
        "zones_json": json.dumps(zones),
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


@login_required
@transaction.atomic
def withdraw_commission(request):
    """✅ NOUVEAU : Retrait de commission BA."""
    if request.method != "POST":
        return redirect("/app/?tab=commissions")
    try:
        ref = create_withdrawal(request.user, request.POST)
        messages.success(request, f"✅ Demande de retrait enregistrée ! Réf: {ref}")
    except Exception as e:
        messages.error(request, f"❌ Échec retrait: {str(e)}")
    return redirect("/app/?tab=commissions")
