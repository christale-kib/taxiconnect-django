"""
Manager Dashboard Services — Données réelles MySQL.
Toutes les fonctions retournent des données prêtes pour le template.
"""
import json
from datetime import timedelta
from collections import defaultdict

from django.utils import timezone
from django.db.models import Sum, Count, Avg, Q, F

from core.models_legacy import (
    BrandAmbassadors,
    Chauffeurs,
    Passagers,
    Commissions,
    Transactions,
    Stations,
    Notifications,
)
from core.models import RetraitCommission
from .models import ObjectiveConfig


# ─── Helpers ───────────────────────────────────────────────────

def _now():
    return timezone.now()


def _month_start():
    return _now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _week_ago():
    return _now() - timedelta(days=7)


def _ba_status(ba_data):
    """Détermine le statut du BA: top, good, watch, risk, new."""
    if ba_data["joined_days"] <= 14:
        return "new"
    activation_rate = ba_data["activation_rate"]
    recruits = ba_data["recruits"]
    if activation_rate >= 70 and recruits >= 5:
        return "top"
    elif activation_rate >= 50 and recruits >= 3:
        return "good"
    elif activation_rate >= 30 or recruits >= 2:
        return "watch"
    return "risk"


def _driver_status_normalized(statut):
    """Normalise le statut chauffeur MySQL."""
    s = (statut or "").upper()
    if s in ("ACTIF", "ACTIVE"):
        return "actif"
    elif s in ("INSCRIT", "EN_ATTENTE"):
        return "en_attente"
    return "inactif"


# ─── Ambassadors ──────────────────────────────────────────────

def get_all_ambassadors():
    """Retourne la liste complète des BA avec stats calculées."""
    now = _now()
    month_start = _month_start()
    bas = BrandAmbassadors.objects.all().order_by("-created_at")
    result = []

    for ba in bas:
        total_chauffeurs = Chauffeurs.objects.filter(ba_id=ba.id).count()
        active_chauffeurs = Chauffeurs.objects.filter(
            ba_id=ba.id
        ).filter(
            Q(statut__in=["ACTIF", "ACTIVE"]) | Q(date_activation__isnull=False)
        ).count()
        total_passagers = Passagers.objects.filter(ba_id=ba.id).count()
        recruits = total_chauffeurs + total_passagers

        # Commissions
        monthly_commission = Commissions.objects.filter(
            ba_id=ba.id, created_at__gte=month_start
        ).aggregate(s=Sum("montant"))["s"] or 0

        total_commission = Commissions.objects.filter(
            ba_id=ba.id
        ).aggregate(s=Sum("montant"))["s"] or 0

        # Activation rate
        activation_rate = round((active_chauffeurs / max(total_chauffeurs, 1)) * 100)

        # Joined days
        joined_days = (now - ba.created_at).days if ba.created_at else 999

        # Target (from config)
        config = ObjectiveConfig.get_config()
        target = config.ba_recruits_target

        # Last week vs this week recruits for trend
        week_ago = _week_ago()
        two_weeks_ago = now - timedelta(days=14)
        this_week_recruits = (
            Chauffeurs.objects.filter(ba_id=ba.id, created_at__gte=week_ago).count()
            + Passagers.objects.filter(ba_id=ba.id, created_at__gte=week_ago).count()
        )
        last_week_recruits = (
            Chauffeurs.objects.filter(ba_id=ba.id, created_at__gte=two_weeks_ago, created_at__lt=week_ago).count()
            + Passagers.objects.filter(ba_id=ba.id, created_at__gte=two_weeks_ago, created_at__lt=week_ago).count()
        )
        trend = 0
        if last_week_recruits > 0:
            trend = round(((this_week_recruits - last_week_recruits) / last_week_recruits) * 100)
        elif this_week_recruits > 0:
            trend = 100

        ba_data = {
            "id": ba.id,
            "name": f"{ba.prenom} {ba.nom}".strip(),
            "city": "",  # Will populate from drivers
            "zone": "",
            "phone": ba.telephone or "",
            "recruits": recruits,
            "active": active_chauffeurs,
            "passengers": total_passagers,
            "commission": float(monthly_commission),
            "commissionTotal": float(total_commission),
            "target": target,
            "streak": ba.serie_jours or 0,
            "joined": ba.created_at.strftime("%Y-%m-%d") if ba.created_at else "",
            "joined_days": joined_days,
            "trend": trend,
            "activation_rate": activation_rate,
        }

        # Get city from first driver's station
        first_driver = Chauffeurs.objects.filter(ba_id=ba.id).select_related("station").first()
        if first_driver and first_driver.station:
            ba_data["city"] = first_driver.station.ville or first_driver.station.nom or ""
            ba_data["zone"] = first_driver.station.quartier or first_driver.station.nom or ""

        ba_data["status"] = _ba_status(ba_data)
        result.append(ba_data)

    return result


# ─── Drivers ──────────────────────────────────────────────────

def get_all_drivers():
    """Retourne la liste complète des chauffeurs avec stats."""
    now = _now()
    week_ago = _week_ago()
    drivers = Chauffeurs.objects.all().select_related("ba", "station").order_by("-created_at")
    result = []

    for d in drivers:
        total_trips = Transactions.objects.filter(chauffeur_id=d.id).count()
        total_revenue = Transactions.objects.filter(
            chauffeur_id=d.id
        ).aggregate(s=Sum("montant"))["s"] or 0
        total_passengers = Transactions.objects.filter(
            chauffeur_id=d.id
        ).values("passager_id").distinct().count()

        weekly_trips = Transactions.objects.filter(
            chauffeur_id=d.id, created_at__gte=week_ago
        ).count()

        # Weekly trips breakdown (7 days)
        weekly_data = []
        for i in range(6, -1, -1):
            day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            count = Transactions.objects.filter(
                chauffeur_id=d.id, created_at__gte=day_start, created_at__lt=day_end
            ).count()
            weekly_data.append(count)

        ba_name = ""
        ba_id = None
        if d.ba:
            ba_name = f"{d.ba.prenom} {d.ba.nom}".strip()
            ba_id = d.ba.id

        city = ""
        if d.station:
            city = d.station.ville or d.station.nom or ""

        status = _driver_status_normalized(d.statut)

        result.append({
            "id": d.id,
            "name": f"{d.prenom} {d.nom}".strip(),
            "phone": d.telephone or "",
            "city": city,
            "plate": d.vehicule_immatriculation or "",
            "vehicle": d.vehicule_marque or "Taxi",
            "ba": ba_name,
            "baId": ba_id,
            "status": status,
            "passengers": total_passengers,
            "trips": total_trips,
            "revenue": float(total_revenue),
            "rating": float(d.note_moyenne) if d.note_moyenne else 0,
            "lastActive": d.updated_at.strftime("%Y-%m-%d") if d.updated_at else "-",
            "enrolled": d.created_at.strftime("%Y-%m-%d") if d.created_at else "",
            "complaints": 0,
            "cancelRate": 0,
            "onTimeRate": 0,
            "avgTrip": float(total_revenue / max(total_trips, 1)),
            "weeklyTrips": weekly_data,
        })

    return result


# ─── Territories ──────────────────────────────────────────────

def get_territories():
    """Agrège les données par ville/station."""
    ambassadors = get_all_ambassadors()
    drivers = get_all_drivers()

    city_data = defaultdict(lambda: {"bas": set(), "recruits": 0, "commission": 0, "active": 0, "growth": 0})

    for ba in ambassadors:
        city = ba["city"] or "Non assigné"
        city_data[city]["bas"].add(ba["id"])
        city_data[city]["recruits"] += ba["recruits"]
        city_data[city]["commission"] += ba["commission"]
        city_data[city]["active"] += ba["active"]

    result = []
    for name, data in city_data.items():
        if not name or name == "Non assigné":
            continue
        result.append({
            "name": name,
            "bas": len(data["bas"]),
            "recruits": data["recruits"],
            "commission": data["commission"],
            "active": data["active"],
            "growth": 0,  # Could compute WoW
        })

    result.sort(key=lambda x: x["commission"], reverse=True)
    return result


# ─── Weekly Enrollments ───────────────────────────────────────

def get_weekly_enrollments():
    """Retourne enrôlements et activations par jour sur 7 jours."""
    now = _now()
    enrollments = []
    activations = []

    for i in range(6, -1, -1):
        day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)

        enrol_count = (
            Chauffeurs.objects.filter(created_at__gte=day_start, created_at__lt=day_end).count()
            + Passagers.objects.filter(created_at__gte=day_start, created_at__lt=day_end).count()
        )
        activation_count = Chauffeurs.objects.filter(
            date_activation__gte=day_start, date_activation__lt=day_end
        ).count()

        enrollments.append(enrol_count)
        activations.append(activation_count)

    return enrollments, activations


# ─── Monthly Revenue ──────────────────────────────────────────

def get_monthly_revenue():
    """Retourne les revenus des 4 derniers mois."""
    now = _now()
    result = []

    for i in range(3, -1, -1):
        month = now.month - i
        year = now.year
        if month <= 0:
            month += 12
            year -= 1
        from datetime import date
        month_start = timezone.make_aware(
            timezone.datetime(year, month, 1)
        )
        if i > 0:
            next_month = month + 1
            next_year = year
            if next_month > 12:
                next_month = 1
                next_year += 1
            month_end = timezone.make_aware(
                timezone.datetime(next_year, next_month, 1)
            )
        else:
            month_end = now

        revenue = Commissions.objects.filter(
            created_at__gte=month_start, created_at__lt=month_end
        ).aggregate(s=Sum("montant"))["s"] or 0
        result.append(float(revenue))

    return result


# ─── Activity Feed ────────────────────────────────────────────

def get_activity_feed(limit=10):
    """Dernières activités: enrôlements, commissions, activations."""
    now = _now()
    activities = []

    # Recent enrollments (drivers)
    recent_drivers = Chauffeurs.objects.select_related("ba").order_by("-created_at")[:5]
    for d in recent_drivers:
        ba_name = f"{d.ba.prenom} {d.ba.nom}".strip() if d.ba else "—"
        driver_name = f"{d.prenom} {d.nom}".strip()
        age = _time_ago(d.created_at, now)
        activities.append({
            "type": "enrol",
            "text": f"<strong>{ba_name}</strong> a enrôlé <strong>{driver_name}</strong>",
            "time": age,
            "color": "var(--green)",
            "timestamp": d.created_at,
        })

    # Recent commissions
    recent_commissions = Commissions.objects.select_related("ba").order_by("-created_at")[:5]
    for c in recent_commissions:
        ba_name = f"{c.ba.prenom} {c.ba.nom}".strip() if c.ba else "—"
        activities.append({
            "type": "commission",
            "text": f"Commission de <strong>{int(c.montant):,} XAF</strong> pour <strong>{ba_name}</strong>".replace(",", " "),
            "time": _time_ago(c.created_at, now),
            "color": "var(--amber)",
            "timestamp": c.created_at,
        })

    # Recent activations
    recent_activations = Chauffeurs.objects.filter(
        date_activation__isnull=False
    ).select_related("ba").order_by("-date_activation")[:3]
    for d in recent_activations:
        ba_name = f"{d.ba.prenom} {d.ba.nom}".strip() if d.ba else "—"
        driver_name = f"{d.prenom} {d.nom}".strip()
        activities.append({
            "type": "activation",
            "text": f"<strong>{driver_name}</strong> activé par <strong>{ba_name}</strong>",
            "time": _time_ago(d.date_activation, now),
            "color": "var(--blue)",
            "timestamp": d.date_activation,
        })

    # Sort by timestamp
    activities.sort(key=lambda x: x["timestamp"] or now, reverse=True)

    # Remove timestamp from output
    for a in activities:
        del a["timestamp"]

    return activities[:limit]


def _time_ago(dt, now):
    """Retourne un texte lisible: 'Il y a 2h', 'Hier 14:00', etc."""
    if not dt:
        return "—"
    diff = now - dt
    hours = diff.total_seconds() / 3600
    if hours < 1:
        return f"Il y a {int(diff.total_seconds() / 60)} min"
    elif hours < 24:
        return f"Il y a {int(hours)}h"
    elif hours < 48:
        return f"Hier {dt.strftime('%H:%M')}"
    else:
        return f"Il y a {int(hours / 24)}j"


# ─── Alerts ───────────────────────────────────────────────────

def get_alerts():
    """Calcule les alertes basées sur la performance des BA et chauffeurs."""
    alerts = []
    ambassadors = get_all_ambassadors()
    config = ObjectiveConfig.get_config()

    for ba in ambassadors:
        # Inactive BA (no recruits in 14 days)
        if ba["status"] == "risk":
            alerts.append({
                "icon": "⚠️",
                "title": f"{ba['name']} — Inactive",
                "desc": f"Statut à risque. {ba['recruits']} recrues, {ba['active']} actifs. Objectif: {ba['target']}.",
                "bg": "var(--red-dim)",
                "action": "Contacter",
                "ba_id": ba["id"],
            })

        # Declining activation rate
        if ba["status"] == "watch" and ba["trend"] < -5:
            alerts.append({
                "icon": "📉",
                "title": f"{ba['name']} — Taux en baisse",
                "desc": f"Activation à {ba['activation_rate']}% ({ba['trend']}% WoW). À suivre.",
                "bg": "var(--amber-dim)",
                "action": "Analyser",
                "ba_id": ba["id"],
            })

        # New BA needing coaching
        if ba["status"] == "new":
            alerts.append({
                "icon": "🆕",
                "title": f"{ba['name']} — Nouveau BA",
                "desc": f"Inscrit il y a {ba['joined_days']} jours. {ba['recruits']} recrue(s). Accompagnement nécessaire.",
                "bg": "var(--blue-dim)",
                "action": "Coacher",
                "ba_id": ba["id"],
            })

        # Target at risk
        if ba["recruits"] < ba["target"] * 0.5 and ba["joined_days"] > 20:
            alerts.append({
                "icon": "🎯",
                "title": f"{ba['name']} — Objectif à risque",
                "desc": f"{ba['recruits']}/{ba['target']} recrues ({round(ba['recruits']/max(ba['target'],1)*100)}%).",
                "bg": "var(--amber-dim)",
                "action": "Relancer",
                "ba_id": ba["id"],
            })

    # Deduplicate by ba_id + icon
    seen = set()
    unique = []
    for a in alerts:
        key = (a.get("ba_id"), a["icon"])
        if key not in seen:
            seen.add(key)
            unique.append(a)

    return unique[:10]


# ─── Objective Config ─────────────────────────────────────────

def get_objective_config():
    """Retourne la config des objectifs au format attendu par le frontend."""
    config = ObjectiveConfig.get_config()
    return {
        "baGlobal": {
            "recruitsTarget": config.ba_recruits_target,
            "activationTarget": config.ba_activation_target,
            "minPassengers": config.ba_min_passengers,
            "commissionPerRecruit": config.ba_commission_per_recruit,
            "bonusStreak3": config.ba_bonus_streak3,
            "bonusStreak7": config.ba_bonus_streak7,
            "bonusTop": config.ba_bonus_top,
            "period": config.ba_period,
        },
        "driverGlobal": {
            "minTripsWeek": config.drv_min_trips_week,
            "minRating": float(config.drv_min_rating),
            "maxCancelRate": config.drv_max_cancel_rate,
            "minOnTimeRate": config.drv_min_ontime_rate,
            "minPassengersWeek": config.drv_min_passengers_week,
            "bonusActive": config.drv_bonus_active,
            "period": config.drv_period,
        },
        "tiers": config.tiers_json or [
            {"name": "Bronze", "minRecruits": 1, "maxRecruits": 4, "commission": 5000, "color": "#CD7F32"},
            {"name": "Argent", "minRecruits": 5, "maxRecruits": 9, "commission": 6000, "color": "#C0C0C0"},
            {"name": "Or", "minRecruits": 10, "maxRecruits": 14, "commission": 7500, "color": "#FFD700"},
            {"name": "Diamant", "minRecruits": 15, "maxRecruits": 999, "commission": 10000, "color": "#00BCD4"},
        ],
    }


# ─── Full Dashboard Data ─────────────────────────────────────

def get_full_dashboard_data():
    """Assemble toutes les données pour le dashboard manager."""
    ambassadors = get_all_ambassadors()
    drivers = get_all_drivers()
    territories = get_territories()
    weekly_enrol, weekly_activations = get_weekly_enrollments()
    monthly_rev = get_monthly_revenue()
    activity = get_activity_feed()
    alerts = get_alerts()
    obj_config = get_objective_config()

    return {
        "ambassadors": ambassadors,
        "drivers": drivers,
        "territories": territories,
        "weeklyEnrolments": weekly_enrol,
        "weeklyActivations": weekly_activations,
        "monthlyRevenue": monthly_rev,
        "activity": activity,
        "alerts": alerts,
        "objConfig": obj_config,
    }
