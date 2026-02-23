import json
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect
from django.http import JsonResponse

from .services import (
    get_merchant_stats, get_recent_merchants,
    get_merchant_leaderboard, create_merchant_enrollment,
)


def merchant_login(request):
    """Page de connexion pour l'app Merchant (mêmes comptes BA)."""
    if request.user.is_authenticated:
        return redirect("merchant_app")
    if request.method == "POST":
        email = (request.POST.get("email") or "").strip().lower()
        password = request.POST.get("password") or ""
        user = authenticate(request, username=email, password=password)
        if user:
            login(request, user)
            return redirect("merchant_app")
        messages.error(request, "Email ou mot de passe incorrect")
    return render(request, "merchant/login.html")


def merchant_logout(request):
    logout(request)
    return redirect("merchant_login")


@login_required(login_url="/merchant/")
def merchant_app(request):
    """Page principale de l'app Merchant."""
    tab = request.GET.get("tab", "dashboard")
    stats = get_merchant_stats(request.user)
    merchants = get_recent_merchants(request.user)
    leaderboard = get_merchant_leaderboard()

    # Build rankings JSON
    ba_name = stats["name"]
    rankings_json = []
    for item in leaderboard:
        rankings_json.append({
            "name": item["name"],
            "total": item["total_merchants"],
            "isYou": item["name"].strip().lower() == ba_name.strip().lower(),
        })

    ctx = {
        "tab": tab,
        "stats": stats,
        "stats_json": json.dumps(stats),
        "merchants_json": json.dumps(merchants),
        "rankings_json": json.dumps(rankings_json),
    }
    return render(request, "merchant/app.html", ctx)


@login_required(login_url="/merchant/")
@transaction.atomic
def enroll_merchant(request):
    """Enrôlement d'un nouveau marchand."""
    if request.method != "POST":
        return redirect("merchant_app")
    try:
        create_merchant_enrollment(request.user, request.POST)
        messages.success(request, "✅ Marchand enregistré avec succès !")
    except Exception as e:
        messages.error(request, f"❌ Échec: {str(e)}")
    return redirect("/merchant/app/?tab=dashboard")


@login_required(login_url="/merchant/")
def merchant_detail_api(request, merchant_id):
    """API: Détails d'un marchand (avec photos)."""
    from .models import Merchant
    from .services import get_ba_email

    email = get_ba_email(request.user)
    try:
        m = Merchant.objects.get(id=merchant_id, ba_email=email)
    except Merchant.DoesNotExist:
        return JsonResponse({"error": "Marchand introuvable"}, status=404)

    return JsonResponse({
        "id": m.id,
        "nom": m.nom,
        "prenom": m.prenom,
        "telephone": m.telephone,
        "adresse": m.adresse,
        "numero_merchant": m.numero_merchant,
        "nom_commerce": m.nom_commerce,
        "statut": m.statut,
        "photo_id_recto": m.photo_id_recto[:100] + "..." if len(m.photo_id_recto) > 100 else m.photo_id_recto,
        "photo_id_verso": m.photo_id_verso[:100] + "..." if len(m.photo_id_verso) > 100 else m.photo_id_verso,
        "photo_rccm": m.photo_rccm[:100] + "..." if len(m.photo_rccm) > 100 else m.photo_rccm,
        "has_photo_id_recto": bool(m.photo_id_recto),
        "has_photo_id_verso": bool(m.photo_id_verso),
        "has_rccm": bool(m.photo_rccm),
        "date": m.created_at.strftime("%d/%m/%Y %H:%M") if m.created_at else "",
    })
