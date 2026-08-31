import pytest
from httpx import AsyncClient

from app.config import settings

HEADERS = {"X-AMI-Secret": settings.AMI_ENDPOINTS_SECRET}


async def _creer_utilisateur_avec_appel(client: AsyncClient) -> dict:
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
    await client.post(f"/api/utilisateurs/{utilisateur['id']}/crediter", json={"montant": "50.00"})
    await client.post(
        "/api/end_call",
        headers=HEADERS,
        json={"channel": "SIP/1001-1", "sip_id": "1001", "duree": 10, "destination": "2002"},
    )
    return utilisateur


@pytest.mark.asyncio
async def test_lister_cdr_inclut_le_nom_de_l_utilisateur(client: AsyncClient) -> None:
    await _creer_utilisateur_avec_appel(client)

    reponse = await client.get("/api/cdr")
    assert reponse.status_code == 200
    cdrs = reponse.json()
    assert len(cdrs) == 1
    assert cdrs[0]["utilisateur_nom"] == "Jean Doe"


@pytest.mark.asyncio
async def test_obtenir_cdr_inclut_le_nom_de_l_utilisateur(client: AsyncClient) -> None:
    await _creer_utilisateur_avec_appel(client)
    cdr_id = (await client.get("/api/cdr")).json()[0]["id"]

    reponse = await client.get(f"/api/cdr/{cdr_id}")
    assert reponse.status_code == 200
    assert reponse.json()["utilisateur_nom"] == "Jean Doe"


@pytest.mark.asyncio
async def test_export_cdr_inclut_le_nom_dans_le_csv(client: AsyncClient) -> None:
    await _creer_utilisateur_avec_appel(client)

    reponse = await client.get("/api/cdr/export")
    assert reponse.status_code == 200
    assert "utilisateur_nom" in reponse.text
    assert "Jean Doe" in reponse.text
