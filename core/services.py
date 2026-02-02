import re
from django.utils import timezone
from django.db.models import Sum, Q
from django.db import IntegrityError
from .models_legacy import (
    BrandAmbassadors,
    Chauffeurs,
    Passagers,
    Commissions,
    Challenges,
    Stations,
)




ZONES = [
    "Brazzaville",
    "Pointe-Noire",
    "Dolisie",
    "N'kayi",
    "Madingou",
    "Oyo",
    "Ouesso",
]


def get_zones():
    return ZONES


    return station
def get_or_create_station_for_zone(zone: str):
    zone = (zone or "").strip()
    if zone not in ZONES:
        raise ValueError("Zone invalide.")
    station = Stations.objects.filter(nom=zone).order_by("id").first()
    if station:
        return station
    return Stations.objects.create(
        nom=zone,
        ville=zone,
        actif=1,
        created_at=timezone.now(),
        updated_at=timezone.now(),
    )

def normalize_and_validate_immatriculation(value: str) -> str:
    raw = (value or "").strip().upper()
    cleaned = re.sub(r"[^A-Z0-9]", "", raw)   # supprime espaces / tirets / etc.
    if len(cleaned) != 6:
        raise ValueError("Immatriculation invalide : 6 caractères requis (ex: AB12CD).")
    return cleaned



def get_ba_from_user(user) -> BrandAmbassadors:
    """
    Associe l'utilisateur Django au BA MySQL via email.
    Si le BA n'existe pas, on le crée (en évitant les collisions telephone unique).
    """
    email = (user.email or user.username or "").strip().lower()
    ba = BrandAmbassadors.objects.filter(email=email).first()
    if ba:
        return ba
    # ⚠️ telephone est UNIQUE dans ta table brand_ambassadors : on doit en fournir un.
    # Si tu stockes le téléphone ailleurs, remplace ici.
    telephone = ""
    if hasattr(user, "ba_profile") and user.ba_profile.telephone:
        telephone = user.ba_profile.telephone.strip()
    if not telephone:
        # fallback unique temporaire (évite crash). Idéalement: rendre téléphone obligatoire à l’inscription.
        telephone = f"TEMP-{user.id}"
    return BrandAmbassadors.objects.create(
        nom=user.last_name or "—",
        prenom=user.first_name or "—",
        email=email,
        telephone=telephone,
        password_hash="",   # si tu fais auth MySQL plus tard, tu stockeras un vrai hash
        niveau="Brand Ambassador",
        statut="ACTIF",
        created_at=timezone.now(),
        updated_at=timezone.now(),
    )


def get_stations():
    qs = Stations.objects.all()
    # On renvoie un format compatible template (id + name)
    out = []
    for s in qs:
        label = s.nom
        if getattr(s, "ville", None):
            label = f"{s.nom} - {s.ville}"
        out.append({"id": s.id, "name": label})
    return out


def get_recent_recruits(user):
    ba = get_ba_from_user(user)
    drivers = Chauffeurs.objects.filter(ba_id=ba.id).order_by("-created_at")[:6]
    passengers = Passagers.objects.filter(ba_id=ba.id).order_by("-created_at")[:6]
    out = []
    for d in drivers:
        is_active = bool(getattr(d, "date_activation", None)) or (getattr(d, "statut", "") in ["ACTIF", "ACTIVE"])
        out.append({
            "id": f"DRV-{d.id}",
            "name": f"{d.prenom} {d.nom}".strip(),
            "type": "Chauffeur",
            "date": d.created_at.strftime("%d/%m/%Y") if d.created_at else "",
            "status": "Activé" if is_active else "Inscrit",
            "commission": 5000,
        })
    for p in passengers:
        is_active = (getattr(p, "statut", "") in ["ACTIF", "ACTIVE"])
        out.append({
            "id": f"PAS-{p.id}",
            "name": f"{p.prenom} {p.nom}".strip(),
            "type": "Passager",
            "date": p.created_at.strftime("%d/%m/%Y") if p.created_at else "",
            "status": "Activé" if is_active else "Inscrit",
            "commission": 500,
        })
    # Tri par date (si vide, reste en bas)
    return out[:10]


def get_dashboard_payload(user):
    ba = get_ba_from_user(user)
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    total_drivers = Chauffeurs.objects.filter(ba_id=ba.id).count()
    active_drivers = Chauffeurs.objects.filter(
        ba_id=ba.id
    ).filter(Q(statut__in=["ACTIF", "ACTIVE"]) | Q(date_activation__isnull=False)).count()
    total_passengers = Passagers.objects.filter(ba_id=ba.id).count()
    monthly_commission = Commissions.objects.filter(
        ba_id=ba.id, created_at__gte=month_start
    ).aggregate(s=Sum("montant"))["s"] or 0
    pending_commission = Commissions.objects.filter(
        ba_id=ba.id, statut__in=["PENDING", "EN_ATTENTE", "EN_COURS"]
    ).aggregate(s=Sum("montant"))["s"] or 0
    monthly_recruits = (
        Chauffeurs.objects.filter(ba_id=ba.id, created_at__gte=month_start).count()
        + Passagers.objects.filter(ba_id=ba.id, created_at__gte=month_start).count()
    )
    target = 100
    if hasattr(user, "ba_profile") and getattr(user.ba_profile, "monthly_target", None):
        target = user.ba_profile.monthly_target
    target_progress = int(min(100, (monthly_recruits / max(1, target)) * 100))
    return {
        "name": f"{ba.prenom} {ba.nom}".strip(),
        "level": ba.niveau or "Brand Ambassador",
        "rank": ba.rang or 0,
        "totalDrivers": total_drivers,
        "activeDrivers": active_drivers,
        "totalPassengers": total_passengers,
        "monthlyCommission": float(monthly_commission),
        "pendingCommission": float(pending_commission),
        "streak": ba.serie_jours or 0,
        "targetProgress": target_progress,
    }


def get_challenges(user):
    # Tu as aussi participations_challenges : on pourra calculer le vrai progress ensuite
    today = timezone.now()
    qs = Challenges.objects.filter(actif=1, date_debut__lte=today, date_fin__gte=today).order_by("date_fin")
    out = []
    for ch in qs:
        out.append({
            "id": ch.id,
            "title": ch.titre,
            "description": ch.description or "",
            "progress": 0,
            "endsIn": ch.date_fin.strftime("%d/%m/%Y") if ch.date_fin else "",
        })
    return out


def get_leaderboard():
    # Option simple : basé sur rang/commission_totale si tu veux
    # Ici on laisse vide ; on peut le brancher ensuite.
    return []


def create_driver_enrollment(user, post):
    ba = get_ba_from_user(user)
    full = (post.get("name") or "").strip()
    parts = full.split()
    nom = parts[-1] if parts else ""
    prenom = " ".join(parts[:-1]) if len(parts) > 1 else full
    phone = (post.get("phone") or "").strip()
    if not phone:
        raise ValueError("Téléphone obligatoire.")
    # ✅ Zone -> station_id (on garde ton schéma existant: Chauffeurs.station_id FK Stations)
    zone = (post.get("zone") or "").strip()
    if not zone:
        raise ValueError("Zone obligatoire.")
    station = get_or_create_station_for_zone(zone)
    # ✅ Adresse
    adresse = (post.get("address") or "").strip() or None
    # ✅ Immatriculation normalisée + 6 caractères
    vehicle_number = normalize_and_validate_immatriculation(post.get("vehicleNumber"))
    vehicle_model = (post.get("vehicleModel") or "N/A").strip()
    marque = (vehicle_model.split(" ")[0] if vehicle_model and vehicle_model != "N/A" else "N/A")
    try:
        d = Chauffeurs.objects.create(
            ba_id=ba.id,
            station_id=station.id,
            nom=nom,
            prenom=prenom,
            telephone=phone,
            email=(post.get("email") or "").strip() or None,
            vehicule_immatriculation=vehicle_number,
            vehicule_marque=marque,
            vehicule_modele=vehicle_model,
            vehicule_couleur="N/A",
            # ⚠️ ce champ n’existe pas encore dans ta table chauffeurs -> voir étape “DB” plus bas
            adresse=adresse,
            photo_profil_url="temp.jpg",
            photo_id_url="temp_id.jpg",
            statut="INSCRIT",
            created_at=timezone.now(),
            updated_at=timezone.now(),
        )
    except IntegrityError as e:
        raise Exception("Téléphone ou immatriculation déjà utilisés.") from e
    Commissions.objects.create(
        ba_id=ba.id,
        type="ENROLL_DRIVER",
        montant=5000,
        recrue_type="CHAUFFEUR",  # ✅ corrigé (ton 'ChauffEUR' est bizarre)
        recrue_id=d.id,
        statut="PENDING",
        created_at=timezone.now(),
    )


def create_passenger_enrollment(user, post):
    ba = get_ba_from_user(user)
    full = (post.get("name") or "").strip()
    parts = full.split()
    nom = parts[-1] if parts else ""
    prenom = " ".join(parts[:-1]) if len(parts) > 1 else full
    try:
        p = Passagers.objects.create(
            ba_id=ba.id,
            nom=nom,
            prenom=prenom,
            telephone=(post.get("phone") or "").strip(),
            email=(post.get("email") or "").strip() or None,
            photo_profil_url="temp.jpg",
            photo_id_url="temp_id.jpg",
            statut="INSCRIT",
            created_at=timezone.now(),
            updated_at=timezone.now(),
        )
    except IntegrityError as e:
        raise Exception("Téléphone passager déjà utilisé.") from e
    Commissions.objects.create(
        ba_id=ba.id,
        type="ENROLL_PASSENGER",
        montant=500,
        recrue_type="PASSAGER",
        recrue_id=p.id,
        statut="PENDING",
        created_at=timezone.now(),
    )