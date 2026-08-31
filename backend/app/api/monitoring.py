from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin, get_db
from app.infrastructure.database.models import Utilisateur

router = APIRouter(
    prefix="/api/monitoring", tags=["monitoring"], dependencies=[Depends(get_current_admin)]
)


from fastapi import Request

@router.get("/resume")
async def resume_monitoring(db: AsyncSession = Depends(get_db)):
    from main import app as application_fastapi
    
    compteur_manager = application_fastapi.state.compteur_manager
    ami_client = application_fastapi.state.ami_client
    
    # Utilisateurs
    total = (await db.execute(select(Utilisateur))).scalars().all()
    actifs = [u for u in total if u.statut == "actif"]
    noms_par_id = {u.id: u.nom_complet for u in total}

    # Appels en cours (compteurs actifs)
    appels_en_cours = len(compteur_manager.compteurs_actifs)

    # Détails des appels en cours
    details_appels = []
    for channel_id, compteur in compteur_manager.compteurs_actifs.items():
        details_appels.append({
            "channel": channel_id,
            "utilisateur_id": compteur.utilisateur_id,
            "utilisateur_nom": noms_par_id.get(compteur.utilisateur_id, "?"),
            "secondes_ecoulees": compteur.secondes_ecoulees,
            "solde_initial": str(compteur.solde_initial),
            "tarif": str(compteur.tarif_par_seconde),
        })
    
    return {
        "ami_connecte": ami_client.connecte,
        "total_utilisateurs": len(total),
        "utilisateurs_actifs": len(actifs),
        "appels_en_cours": appels_en_cours,
        "details_appels": details_appels,
    }
