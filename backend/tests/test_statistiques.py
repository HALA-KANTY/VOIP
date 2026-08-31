import pytest
from httpx import AsyncClient

from app.config import settings


async def _creer_utilisateur_et_appel(client: AsyncClient) -> str:
    utilisateur = (
        await client.post(
            "/api/utilisateurs",
            json={
                "username": "jdoe",
                "nom_complet": "Jean Doe",
                "password": "motdepasse123",
                "sip_id": "1001",
            },
        )
    ).json()
    await client.post(f"/api/utilisateurs/{utilisateur['id']}/crediter", json={"montant": "100.00"})
    return utilisateur["sip_id"]


@pytest.mark.asyncio
async def test_statistiques_appels_sur_base_vide(client: AsyncClient) -> None:
    reponse = await client.get("/api/statistiques/appels")
    assert reponse.status_code == 200
    assert reponse.json()["total_appels"] == 0


@pytest.mark.asyncio
async def test_statistiques_revenus_ne_leve_pas_erreur(client: AsyncClient) -> None:
    # Regression : cast(CDR.date_appel, Date) plante sur SQLite (fromisoformat sur non-str).
    # func.date(...) doit fonctionner de la meme facon sur SQLite et PostgreSQL.
    reponse = await client.get("/api/statistiques/revenus")
    assert reponse.status_code == 200
    assert reponse.json() == []


@pytest.mark.asyncio
async def test_statistiques_destinations_sur_base_vide(client: AsyncClient) -> None:
    reponse = await client.get("/api/statistiques/destinations")
    assert reponse.status_code == 200
    assert reponse.json() == []


@pytest.mark.asyncio
async def test_statistiques_utilisateurs(client: AsyncClient) -> None:
    await _creer_utilisateur_et_appel(client)

    reponse = await client.get("/api/statistiques/utilisateurs")
    assert reponse.status_code == 200
    donnees = reponse.json()
    assert donnees["total_utilisateurs"] == 1
    assert donnees["utilisateurs_actifs"] == 1
    assert donnees["solde_total"] == "100.00"


@pytest.mark.asyncio
async def test_revenus_et_destinations_apres_un_appel(client: AsyncClient) -> None:
    sip_id = await _creer_utilisateur_et_appel(client)

    reponse = await client.post(
        "/api/end_call",
        headers={"X-AMI-Secret": settings.AMI_ENDPOINTS_SECRET},
        json={
            "channel": "SIP/test-1",
            "sip_id": sip_id,
            "duree": 30,
            "destination": "0341234567",
        },
    )
    assert reponse.status_code == 200

    revenus = (await client.get("/api/statistiques/revenus")).json()
    assert len(revenus) == 1
    assert revenus[0]["revenu"] == "30.00"

    destinations = (await client.get("/api/statistiques/destinations")).json()
    assert destinations == [{"destination": "0341234567", "nombre_appels": 1, "cout_total": "30.00"}]

    appels = (await client.get("/api/statistiques/appels")).json()
    assert appels["total_appels"] == 1
    assert appels["appels_termines"] == 1
