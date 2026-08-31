import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_creer_puis_lister_utilisateur(client: AsyncClient) -> None:
    reponse = await client.post(
        "/api/utilisateurs",
        json={"username": "jdoe", "nom_complet": "Jean Doe", "password": "motdepasse123"},
    )
    assert reponse.status_code == 201
    utilisateur = reponse.json()
    assert utilisateur["username"] == "jdoe"
    assert utilisateur["solde"] == "0.00"

    reponse = await client.get("/api/utilisateurs")
    assert reponse.status_code == 200
    assert len(reponse.json()) == 1


@pytest.mark.asyncio
async def test_creer_utilisateur_username_duplique_echoue(client: AsyncClient) -> None:
    payload = {"username": "jdoe", "nom_complet": "Jean Doe", "password": "motdepasse123"}
    assert (await client.post("/api/utilisateurs", json=payload)).status_code == 201
    reponse = await client.post("/api/utilisateurs", json=payload)
    assert reponse.status_code == 409


@pytest.mark.asyncio
async def test_crediter_et_debiter_solde(client: AsyncClient) -> None:
    creation = await client.post(
        "/api/utilisateurs",
        json={"username": "jdoe", "nom_complet": "Jean Doe", "password": "motdepasse123"},
    )
    utilisateur_id = creation.json()["id"]

    reponse = await client.post(f"/api/utilisateurs/{utilisateur_id}/crediter", json={"montant": "50.00"})
    assert reponse.status_code == 200
    assert reponse.json()["solde"] == "50.00"

    reponse = await client.post(f"/api/utilisateurs/{utilisateur_id}/debiter", json={"montant": "20.00"})
    assert reponse.status_code == 200
    assert reponse.json()["solde"] == "30.00"

    reponse = await client.post(f"/api/utilisateurs/{utilisateur_id}/debiter", json={"montant": "999.00"})
    assert reponse.status_code == 400


@pytest.mark.asyncio
async def test_obtenir_utilisateur_inconnu_retourne_404(client: AsyncClient) -> None:
    reponse = await client.get("/api/utilisateurs/9999")
    assert reponse.status_code == 404


@pytest.mark.asyncio
async def test_supprimer_utilisateur(client: AsyncClient) -> None:
    creation = await client.post(
        "/api/utilisateurs",
        json={"username": "jdoe", "nom_complet": "Jean Doe", "password": "motdepasse123"},
    )
    utilisateur_id = creation.json()["id"]

    reponse = await client.delete(f"/api/utilisateurs/{utilisateur_id}")
    assert reponse.status_code == 204
    assert (await client.get(f"/api/utilisateurs/{utilisateur_id}")).status_code == 404


@pytest.mark.asyncio
async def test_sip_id_sans_secret_genere_un_secret_automatiquement(client: AsyncClient) -> None:
    reponse = await client.post(
        "/api/utilisateurs",
        json={
            "username": "jdoe",
            "nom_complet": "Jean Doe",
            "password": "motdepasse123",
            "sip_id": "1001",
        },
    )
    assert reponse.status_code == 201
    utilisateur = reponse.json()
    assert utilisateur["sip_id"] == "1001"
    assert utilisateur["sip_secret"] is not None
    assert len(utilisateur["sip_secret"]) >= 8


@pytest.mark.asyncio
async def test_sans_sip_id_fourni_un_sip_id_est_attribue_automatiquement(client: AsyncClient) -> None:
    # Un sip_id (et donc un secret) est desormais toujours attribue selon la
    # plage du type d'utilisateur (PLAGES_SIP), meme si non fourni explicitement.
    reponse = await client.post(
        "/api/utilisateurs",
        json={"username": "jdoe", "nom_complet": "Jean Doe", "password": "motdepasse123"},
    )
    utilisateur = reponse.json()
    assert utilisateur["sip_id"] is not None
    assert utilisateur["sip_id"].startswith("2")  # plage "normal" = 2000+
    assert utilisateur["sip_secret"] is not None


@pytest.mark.asyncio
async def test_secret_sip_fourni_est_conserve(client: AsyncClient) -> None:
    reponse = await client.post(
        "/api/utilisateurs",
        json={
            "username": "jdoe",
            "nom_complet": "Jean Doe",
            "password": "motdepasse123",
            "sip_id": "1001",
            "sip_secret": "MonSecretChoisi123",
        },
    )
    assert reponse.json()["sip_secret"] == "MonSecretChoisi123"


@pytest.mark.asyncio
async def test_changer_sip_id_via_update_conserve_un_secret(client: AsyncClient) -> None:
    creation = await client.post(
        "/api/utilisateurs",
        json={"username": "jdoe", "nom_complet": "Jean Doe", "password": "motdepasse123"},
    )
    utilisateur_id = creation.json()["id"]
    assert creation.json()["sip_secret"] is not None

    reponse = await client.put(f"/api/utilisateurs/{utilisateur_id}", json={"sip_id": "1002"})
    assert reponse.status_code == 200
    assert reponse.json()["sip_id"] == "1002"
    assert reponse.json()["sip_secret"] is not None


@pytest.mark.asyncio
async def test_effacer_sip_id_via_update(client: AsyncClient) -> None:
    creation = await client.post(
        "/api/utilisateurs",
        json={"username": "jdoe", "nom_complet": "Jean Doe", "password": "motdepasse123"},
    )
    utilisateur_id = creation.json()["id"]

    reponse = await client.put(f"/api/utilisateurs/{utilisateur_id}", json={"sip_id": None})
    assert reponse.status_code == 200
    assert reponse.json()["sip_id"] is None


@pytest.mark.asyncio
async def test_regenerer_secret_sip(client: AsyncClient) -> None:
    creation = await client.post(
        "/api/utilisateurs",
        json={
            "username": "jdoe",
            "nom_complet": "Jean Doe",
            "password": "motdepasse123",
            "sip_id": "1001",
        },
    )
    utilisateur_id = creation.json()["id"]
    ancien_secret = creation.json()["sip_secret"]

    reponse = await client.post(f"/api/utilisateurs/{utilisateur_id}/regenerer_secret_sip")
    assert reponse.status_code == 200
    assert reponse.json()["sip_secret"] != ancien_secret


@pytest.mark.asyncio
async def test_regenerer_secret_sip_sans_sip_id_echoue(client: AsyncClient) -> None:
    creation = await client.post(
        "/api/utilisateurs",
        json={"username": "jdoe", "nom_complet": "Jean Doe", "password": "motdepasse123"},
    )
    utilisateur_id = creation.json()["id"]
    await client.put(f"/api/utilisateurs/{utilisateur_id}", json={"sip_id": None})

    reponse = await client.post(f"/api/utilisateurs/{utilisateur_id}/regenerer_secret_sip")
    assert reponse.status_code == 400
