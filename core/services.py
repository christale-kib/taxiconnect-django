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
    station_id = int(post.get("station_id") or 1)
    vehicle_number = (post.get("vehicleNumber") or "").strip().upper()
    vehicle_model = (post.get("vehicleModel") or "N/A").strip()
    try:
        d = Chauffeurs.objects.create(
            ba_id=ba.id,
            station_id=station_id,
            nom=nom,
            prenom=prenom,
            telephone=(post.get("phone") or "").strip(),
            email=(post.get("email") or "").strip() or None,
            vehicule_immatriculation=vehicle_number,
            vehicule_marque=vehicle_model.split(" ")[0],
            vehicule_modele=vehicle_model,
            vehicule_couleur="N/A",
            photo_profil_url="temp.jpg",
            photo_id_url="temp_id.jpg",
            statut="INSCRIT",
            created_at=timezone.now(),
            updated_at=timezone.now(),
        )
    except IntegrityError as e:
        # collisions uniques: telephone / immatriculation
        raise Exception("Téléphone ou immatriculation déjà utilisés.") from e
    Commissions.objects.create(
        ba_id=ba.id,
        type="ENROLL_DRIVER",
        montant=5000,
        recrue_type="ChauffEUR",
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