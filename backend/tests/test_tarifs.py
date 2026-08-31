import pytest
from httpx import AsyncClient

from app.config import settings


@pytest.mark.asyncio
async def test_tarif_actif_sans_tarif_en_base_retourne_le_defaut(client: AsyncClient) -> None:
    reponse = await client.get("/api/tarifs/actif")
    assert reponse.status_code == 200
    assert reponse.json()["montant_par_seconde"] == str(settings.TARIF_DEFAUT)


@pytest.mark.asyncio
async def test_changer_tarif_est_repercute_sur_tarif_actif(client: AsyncClient) -> None:
    reponse = await client.post("/api/tarifs", json={"montant_par_seconde": "2.50"})
    assert reponse.status_code == 201

    reponse = await client.get("/api/tarifs/actif")
    assert reponse.json()["montant_par_seconde"] == "2.50"


@pytest.mark.asyncio
async def test_changer_tarif_desactive_l_ancien(client: AsyncClient) -> None:
    await client.post("/api/tarifs", json={"montant_par_seconde": "1.00"})
    await client.post("/api/tarifs", json={"montant_par_seconde": "3.00"})

    reponse = await client.get("/api/tarifs/actif")
    # Un seul tarif actif a la fois : le dernier change gagne, l'ancien ne doit
    # plus influencer check_balance/end_call.
    assert reponse.json()["montant_par_seconde"] == "3.00"


@pytest.mark.asyncio
async def test_changer_tarif_est_utilise_par_check_balance(client: AsyncClient) -> None:
    await client.post(
        "/api/utilisateurs",
        json={
            "username": "jdoe",
            "nom_complet": "Jean Doe",
            "password": "motdepasse123",
            "sip_id": "1001",
        },
    )
    await client.post("/api/tarifs", json={"montant_par_seconde": "5.00"})

    reponse = await client.get(
        "/api/check_balance",
        params={"sip_id": "1001"},
        headers={"X-AMI-Secret": settings.AMI_ENDPOINTS_SECRET},
    )
    assert reponse.json()["tarif_par_seconde"] == "5.00"
