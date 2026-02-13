import json
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST

from .models import ManagerProfile, ObjectiveConfig
from .services import get_full_dashboard_data


def _is_manager(user):
    return hasattr(user, "manager_profile")


def manager_login(request):
    if request.user.is_authenticated and _is_manager(request.user):
        return redirect("manager_dashboard")
    if request.method == "POST":
        email = (request.POST.get("email") or "").strip().lower()
        password = request.POST.get("password") or ""
        user = authenticate(request, username=email, password=password)
        if user:
            if not _is_manager(user):
                messages.error(request, "Ce compte n'est pas un compte manager.")
            else:
                login(request, user)
                return redirect("manager_dashboard")
        else:
            messages.error(request, "Email ou mot de passe incorrect.")
    return render(request, "manager/login.html")


def manager_logout(request):
    logout(request)
    return redirect("manager_login")


@login_required
def manager_dashboard(request):
    """Vue principale du dashboard manager — sert le template SPA avec données JSON."""
    if not _is_manager(request.user):
        messages.error(request, "Accès réservé aux managers.")
        return redirect("manager_login")

    data = get_full_dashboard_data()

    return render(request, "manager/dashboard.html", {
        "dashboard_data_json": json.dumps(data, ensure_ascii=False, default=str),
        "manager_name": f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
    })


@login_required
@require_POST
def update_config(request):
    """API: Met à jour la config des objectifs."""
    if not _is_manager(request.user):
        return JsonResponse({"error": "Non autorisé"}, status=403)

    try:
        body = json.loads(request.body)
        config = ObjectiveConfig.get_config()

        # BA config
        if "baGlobal" in body:
            bg = body["baGlobal"]
            config.ba_recruits_target = bg.get("recruitsTarget", config.ba_recruits_target)
            config.ba_activation_target = bg.get("activationTarget", config.ba_activation_target)
            config.ba_min_passengers = bg.get("minPassengers", config.ba_min_passengers)
            config.ba_commission_per_recruit = bg.get("commissionPerRecruit", config.ba_commission_per_recruit)
            config.ba_bonus_streak3 = bg.get("bonusStreak3", config.ba_bonus_streak3)
            config.ba_bonus_streak7 = bg.get("bonusStreak7", config.ba_bonus_streak7)
            config.ba_bonus_top = bg.get("bonusTop", config.ba_bonus_top)

        # Driver config
        if "driverGlobal" in body:
            dg = body["driverGlobal"]
            config.drv_min_trips_week = dg.get("minTripsWeek", config.drv_min_trips_week)
            config.drv_min_rating = dg.get("minRating", config.drv_min_rating)
            config.drv_max_cancel_rate = dg.get("maxCancelRate", config.drv_max_cancel_rate)
            config.drv_min_ontime_rate = dg.get("minOnTimeRate", config.drv_min_ontime_rate)
            config.drv_min_passengers_week = dg.get("minPassengersWeek", config.drv_min_passengers_week)
            config.drv_bonus_active = dg.get("bonusActive", config.drv_bonus_active)

        # Tiers
        if "tiers" in body:
            config.tiers_json = body["tiers"]

        config.save()
        return JsonResponse({"ok": True})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@login_required
def api_dashboard_data(request):
    """API: Retourne les données du dashboard en JSON (pour refresh AJAX)."""
    if not _is_manager(request.user):
        return JsonResponse({"error": "Non autorisé"}, status=403)
    data = get_full_dashboard_data()
    return JsonResponse(data, safe=False)
