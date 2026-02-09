import re
import uuid
from django.utils import timezone
from django.db.models import Sum, Q, Count
from django.db import IntegrityError
from core.models_legacy import (
    Chauffeurs,
    Passagers,
    Stations,
    Transactions,
)
from core.models import TaxiProfile
from core.services import ZONES, get_or_create_station_for_zone, normalize_and_validate_immatriculation
from .models import TaxiEnrollment


def get_chauffeur_from_user(user) -> Chauffeurs:
    """
    Récupère le chauffeur MySQL lié à l'utilisateur Django via TaxiProfile.
    """
    if not hasattr(user, "taxi_profile"):
        raise ValueError("Pas de profil taxi associé.")
    profile = user.taxi_profile
    if not profile.chauffeur_id:
        raise ValueError("Pas de chauffeur_id dans le profil taxi.")
    ch = Chauffeurs.objects.filter(id=profile.chauffeur_id).first()
    if not ch:
        raise ValueError("Chauffeur introuvable en base.")
    return ch


def _compute_chauffeur_rank(chauffeur):
    """
    ✅ RANG CHAUFFEUR = basé sur son NOMBRE DE PAIEMENTS (transactions).
    """
    my_count = Transactions.objects.filter(chauffeur_id=chauffeur.id).count()
    # Compter pour tous les chauffeurs
    all_chauffeurs = Chauffeurs.objects.all()
    counts = []
    for ch in all_chauffeurs:
        c = Transactions.objects.filter(chauffeur_id=ch.id).count()
        counts.append((ch.id, c))
    counts.sort(key=lambda x: x[1], reverse=True)
    rank = 1
    for ch_id, count in counts:
        if ch_id == chauffeur.id:
            return rank
        rank += 1
    return rank


def get_taxi_dashboard(user):
    """Dashboard pour un chauffeur connecté."""
    ch = get_chauffeur_from_user(user)
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Stats paiements
    total_transactions = Transactions.objects.filter(chauffeur_id=ch.id).count()
    monthly_transactions = Transactions.objects.filter(
        chauffeur_id=ch.id, created_at__gte=month_start
    ).count()
    total_revenue = Transactions.objects.filter(
        chauffeur_id=ch.id
    ).aggregate(s=Sum("montant"))["s"] or 0
    monthly_revenue = Transactions.objects.filter(
        chauffeur_id=ch.id, created_at__gte=month_start
    ).aggregate(s=Sum("montant"))["s"] or 0

    # Stats enrôlements taxi
    total_recruits = TaxiEnrollment.objects.filter(parrain_chauffeur_id=ch.id).count()

    rank = _compute_chauffeur_rank(ch)

    return {
        "name": f"{ch.prenom} {ch.nom}".strip(),
        "telephone": ch.telephone or "",
        "rank": rank,
        "totalTransactions": total_transactions,
        "monthlyTransactions": monthly_transactions,
        "totalRevenue": float(total_revenue),
        "monthlyRevenue": float(monthly_revenue),
        "totalRecruits": total_recruits,
        "note": float(ch.note_moyenne) if ch.note_moyenne else 0,
        "immatriculation": ch.vehicule_immatriculation or "",
    }


def get_taxi_leaderboard():
    """
    ✅ Leaderboard Taxi = classement par nombre de PAIEMENTS (transactions).
    """
    all_chauffeurs = Chauffeurs.objects.filter(statut__in=["ACTIF", "ACTIVE", "INSCRIT"])
    data = []
    for ch in all_chauffeurs:
        count = Transactions.objects.filter(chauffeur_id=ch.id).count()
        data.append({
            "name": f"{ch.prenom} {ch.nom}".strip(),
            "total_payments": count,
        })
    data.sort(key=lambda x: x["total_payments"], reverse=True)
    for i, item in enumerate(data):
        item["rank"] = i + 1
    return data[:20]


def get_taxi_recent_recruits(user):
    """Liste des taxis enrôlés par ce chauffeur."""
    ch = get_chauffeur_from_user(user)
    enrollments = TaxiEnrollment.objects.filter(
        parrain_chauffeur_id=ch.id
    ).order_by("-created_at")[:10]
    out = []
    for e in enrollments:
        recrue = Chauffeurs.objects.filter(id=e.recrue_chauffeur_id).first()
        if recrue:
            out.append({
                "id": f"TAXI-{recrue.id}",
                "name": f"{recrue.prenom} {recrue.nom}".strip(),
                "phone": recrue.telephone or "",
                "immat": recrue.vehicule_immatriculation or "",
                "date": e.created_at.strftime("%d/%m/%Y") if e.created_at else "",
                "status": recrue.statut or "INSCRIT",
            })
    return out


def get_taxi_recent_payments(user):
    """Dernières transactions du chauffeur."""
    ch = get_chauffeur_from_user(user)
    txs = Transactions.objects.filter(chauffeur_id=ch.id).order_by("-created_at")[:10]
    out = []
    for tx in txs:
        passager_name = "—"
        if tx.passager_id:
            p = Passagers.objects.filter(id=tx.passager_id).first()
            if p:
                passager_name = f"{p.prenom} {p.nom}".strip()
        out.append({
            "id": tx.id,
            "passager": passager_name,
            "montant": float(tx.montant),
            "statut": tx.statut or "PENDING",
            "date": tx.created_at.strftime("%d/%m/%Y %H:%M") if tx.created_at else "",
            "methode": tx.methode_paiement or "—",
            "reference": tx.reference_paiement or "",
        })
    return out


def create_taxi_enrollment(user, post):
    """
    Un chauffeur enrôle un AUTRE taxi (chauffeur).
    """
    parrain = get_chauffeur_from_user(user)

    full = (post.get("name") or "").strip()
    parts = full.split()
    nom = parts[-1] if parts else ""
    prenom = " ".join(parts[:-1]) if len(parts) > 1 else full
    phone = (post.get("phone") or "").strip()
    if not phone:
        raise ValueError("Téléphone obligatoire.")

    zone = (post.get("zone") or "").strip()
    if not zone:
        raise ValueError("Zone obligatoire.")
    station = get_or_create_station_for_zone(zone)

    adresse = (post.get("address") or "").strip() or None
    vehicle_number = normalize_and_validate_immatriculation(post.get("vehicleNumber"))
    vehicle_model = (post.get("vehicleModel") or "N/A").strip()
    marque = vehicle_model.split(" ")[0] if vehicle_model and vehicle_model != "N/A" else "N/A"

    try:
        recrue = Chauffeurs.objects.create(
            ba_id=parrain.ba_id,  # Même BA que le parrain
            station_id=station.id,
            nom=nom,
            prenom=prenom,
            telephone=phone,
            email=(post.get("email") or "").strip() or None,
            vehicule_immatriculation=vehicle_number,
            vehicule_marque=marque,
            vehicule_modele=vehicle_model,
            vehicule_couleur="N/A",
            adresse=adresse,
            photo_profil_url="temp.jpg",
            photo_id_url="temp_id.jpg",
            statut="INSCRIT",
            created_at=timezone.now(),
            updated_at=timezone.now(),
        )
    except IntegrityError as e:
        raise Exception("Téléphone ou immatriculation déjà utilisés.") from e

    # Tracer l'enrôlement taxi→taxi
    TaxiEnrollment.objects.create(
        parrain_chauffeur_id=parrain.id,
        recrue_chauffeur_id=recrue.id,
    )
    return recrue


def create_payment(user, post):
    """
    Un chauffeur initie un PAIEMENT pour un passager.
    Crée une Transaction (pas un enrôlement passager).
    """
    ch = get_chauffeur_from_user(user)

    phone_passager = (post.get("phone_passager") or "").strip()
    montant = post.get("montant")
    methode = (post.get("methode") or "AIRTEL_MONEY").strip()

    if not montant or float(montant) <= 0:
        raise ValueError("Montant invalide.")
    if not phone_passager:
        raise ValueError("Téléphone passager obligatoire.")

    # Chercher le passager par téléphone (optionnel — peut être anonyme)
    passager = Passagers.objects.filter(telephone=phone_passager).first()
    passager_id = passager.id if passager else None

    ref = f"TX-{uuid.uuid4().hex[:8].upper()}"

    tx = Transactions.objects.create(
        chauffeur_id=ch.id,
        passager_id=passager_id,
        montant=float(montant),
        commission_taux=10.00,  # 10% par défaut
        commission_montant=float(montant) * 0.10,
        statut="PENDING",
        methode_paiement=methode,
        reference_paiement=ref,
        created_at=timezone.now(),
        updated_at=timezone.now(),
    )
    return tx, ref
