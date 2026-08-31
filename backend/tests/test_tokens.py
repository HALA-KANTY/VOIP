import pytest
from httpx import AsyncClient


async def _creer_utilisateur(client: AsyncClient) -> int:
    reponse = await client.post(
        "/api/utilisateurs",
        json={"username": "jdoe", "nom_complet": "Jean Doe", "password": "motdepasse123"},
    )
    return reponse.json()["id"]


@pytest.mark.asyncio
async def test_generer_puis_verifier_token(client: AsyncClient) -> None:
    reponse = await client.post("/api/tokens/generer", json={"montant": "25.00"})
    assert reponse.status_code == 201
    token = reponse.json()
    assert token["statut"] == "non_utilise"

    reponse = await client.get(f"/api/tokens/{token['code']}")
    assert reponse.status_code == 200
    assert reponse.json()["code"] == token["code"]


@pytest.mark.asyncio
async def test_verifier_token_inconnu_retourne_404(client: AsyncClient) -> None:
    reponse = await client.get("/api/tokens/CODE_INEXISTANT")
    assert reponse.status_code == 404


@pytest.mark.asyncio
async def test_valider_token_credite_le_solde_et_le_marque_utilise(client: AsyncClient) -> None:
    utilisateur_id = await _creer_utilisateur(client)
    token = (await client.post("/api/tokens/generer", json={"montant": "25.00"})).json()

    reponse = await client.post(
        "/api/tokens/valider", json={"code": token["code"], "utilisateur_id": utilisateur_id}
    )
    assert reponse.status_code == 200
    assert reponse.json()["montant"] == "25.00"

    solde = await client.get(f"/api/utilisateurs/{utilisateur_id}/solde")
    assert solde.json()["solde"] == "25.00"


@pytest.mark.asyncio
async def test_token_deja_utilise_ne_peut_pas_etre_revalide(client: AsyncClient) -> None:
    utilisateur_id = await _creer_utilisateur(client)
    token = (await client.post("/api/tokens/generer", json={"montant": "10.00"})).json()

    premiere = await client.post(
        "/api/tokens/valider", json={"code": token["code"], "utilisateur_id": utilisateur_id}
    )
    assert premiere.status_code == 200

    seconde = await client.post(
        "/api/tokens/valider", json={"code": token["code"], "utilisateur_id": utilisateur_id}
    )
    assert seconde.status_code == 400


@pytest.mark.asyncio
async def test_rechargement_via_endpoint_dedie(client: AsyncClient) -> None:
    utilisateur_id = await _creer_utilisateur(client)
    token = (await client.post("/api/tokens/generer", json={"montant": "15.00"})).json()

    reponse = await client.post(
        "/api/rechargements", json={"utilisateur_id": utilisateur_id, "code_token": token["code"]}
    )
    assert reponse.status_code == 201
    assert reponse.json()["montant"] == "15.00"

    liste = await client.get("/api/rechargements")
    assert len(liste.json()) == 1


@pytest.mark.asyncio
async def test_generer_lot_retourne_les_codes_generes(client: AsyncClient) -> None:
    reponse = await client.post("/api/tokens/bulk", json={"montant": "20.00", "quantite": 3})
    assert reponse.status_code == 201

    donnees = reponse.json()
    assert donnees["succes"] is True
    assert donnees["montant"] == "20.00"
    assert len(donnees["codes"]) == 3
    assert all(len(code) == 12 and code.isdigit() for code in donnees["codes"])
    assert len(set(donnees["codes"])) == 3


@pytest.mark.asyncio
async def test_generer_token_code_a_12_chiffres(client: AsyncClient) -> None:
    token = (await client.post("/api/tokens/generer", json={"montant": "10.00"})).json()
    assert len(token["code"]) == 12
    assert token["code"].isdigit()


@pytest.mark.asyncio
async def test_supprimer_token_non_utilise(client: AsyncClient) -> None:
    token = (await client.post("/api/tokens/generer", json={"montant": "10.00"})).json()

    reponse = await client.delete(f"/api/tokens/{token['id']}")
    assert reponse.status_code == 204
    assert (await client.get(f"/api/tokens/{token['code']}")).status_code == 404


@pytest.mark.asyncio
async def test_supprimer_token_deja_utilise_refuse(client: AsyncClient) -> None:
    utilisateur_id = await _creer_utilisateur(client)
    token = (await client.post("/api/tokens/generer", json={"montant": "10.00"})).json()
    await client.post("/api/tokens/valider", json={"code": token["code"], "utilisateur_id": utilisateur_id})

    reponse = await client.delete(f"/api/tokens/{token['id']}")
    assert reponse.status_code == 400
    assert (await client.get(f"/api/tokens/{token['code']}")).status_code == 200


@pytest.mark.asyncio
async def test_supprimer_token_inconnu_404(client: AsyncClient) -> None:
    reponse = await client.delete("/api/tokens/999999")
    assert reponse.status_code == 404
