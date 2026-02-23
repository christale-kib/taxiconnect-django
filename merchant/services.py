from django.db import IntegrityError
from django.db.models import Count, Q

from .models import Merchant
from core.models_legacy import BrandAmbassadors


def get_ba_email(user):
    """Récupère l'email du BA connecté."""
    return (user.email or user.username or "").strip().lower()


def get_ba_from_user(user):
    """Retrouve le BA MySQL via l'email."""
    email = get_ba_email(user)
    return BrandAmbassadors.objects.filter(email=email).first()


def get_merchant_stats(user):
    """Statistiques marchands pour le BA connecté."""
    email = get_ba_email(user)
    ba = get_ba_from_user(user)

    total = Merchant.objects.filter(ba_email=email).count()
    actifs = Merchant.objects.filter(ba_email=email, statut="ACTIF").count()
    inscrits = Merchant.objects.filter(ba_email=email, statut="INSCRIT").count()

    return {
        "name": f"{ba.prenom} {ba.nom}".strip() if ba else user.get_full_name() or user.username,
        "level": ba.niveau if ba else "Brand Ambassador",
        "totalMerchants": total,
        "activeMerchants": actifs,
        "pendingMerchants": inscrits,
    }


def get_recent_merchants(user, limit=20):
    """Liste des marchands récemment recrutés par ce BA."""
    email = get_ba_email(user)
    qs = Merchant.objects.filter(ba_email=email).order_by("-created_at")[:limit]
    out = []
    for m in qs:
        out.append({
            "id": m.id,
            "nom": m.nom,
            "prenom": m.prenom,
            "name": f"{m.prenom} {m.nom}".strip(),
            "telephone": m.telephone,
            "adresse": m.adresse,
            "numero_merchant": m.numero_merchant,
            "nom_commerce": m.nom_commerce,
            "status": m.statut.lower(),
            "date": m.created_at.strftime("%d/%m/%Y") if m.created_at else "",
            "has_photo_id": bool(m.photo_id_recto),
            "has_rccm": bool(m.photo_rccm),
        })
    return out


def get_merchant_leaderboard():
    """Classement des BA par nombre de marchands recrutés."""
    all_bas = BrandAmbassadors.objects.filter(statut__in=["ACTIF", "ACTIVE"])
    data = []
    for ba in all_bas:
        email = (ba.email or "").strip().lower()
        total = Merchant.objects.filter(ba_email=email).count()
        if total > 0:
            data.append({
                "name": f"{ba.prenom} {ba.nom}".strip(),
                "total_merchants": total,
            })
    data.sort(key=lambda x: x["total_merchants"], reverse=True)
    for i, item in enumerate(data):
        item["rank"] = i + 1
    return data[:10]


def create_merchant_enrollment(user, post):
    """Créer un marchand recruté par le BA."""
    email = get_ba_email(user)

    nom = (post.get("nom") or "").strip()
    prenom = (post.get("prenom") or "").strip()
    telephone = (post.get("telephone") or "").strip()
    adresse = (post.get("adresse") or "").strip()
    numero_merchant = (post.get("numero_merchant") or "").strip()
    nom_commerce = (post.get("nom_commerce") or "").strip()

    # Photos (base64)
    photo_id_recto = (post.get("photo_id_recto") or "").strip()
    photo_id_verso = (post.get("photo_id_verso") or "").strip()
    photo_rccm = (post.get("photo_rccm") or "").strip()

    # Validations
    if not nom:
        raise ValueError("Le nom est obligatoire.")
    if not prenom:
        raise ValueError("Le prénom est obligatoire.")
    if not telephone:
        raise ValueError("Le téléphone est obligatoire.")
    if not numero_merchant:
        raise ValueError("Le numéro marchand est obligatoire.")
    if not nom_commerce:
        raise ValueError("Le nom du commerce est obligatoire.")

    try:
        merchant = Merchant.objects.create(
            ba_email=email,
            nom=nom,
            prenom=prenom,
            telephone=telephone,
            adresse=adresse,
            numero_merchant=numero_merchant,
            nom_commerce=nom_commerce,
            photo_id_recto=photo_id_recto,
            photo_id_verso=photo_id_verso,
            photo_rccm=photo_rccm,
            statut="INSCRIT",
        )
    except IntegrityError as e:
        if "telephone" in str(e).lower():
            raise Exception("Ce numéro de téléphone est déjà enregistré.") from e
        if "numero_merchant" in str(e).lower():
            raise Exception("Ce numéro marchand est déjà enregistré.") from e
        raise Exception("Données en doublon détectées.") from e

    return merchant
