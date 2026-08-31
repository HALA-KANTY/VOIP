import pytest
from httpx import AsyncClient

from app.config import settings

HEADERS = {"X-AMI-Secret": settings.AMI_ENDPOINTS_SECRET}


async def _creer_utilisateur(client: AsyncClient, sip_id: str = "1001") -> dict:
    return (
        await client.post(
            "/api/utilisateurs",
            json={
                "username": f"user{sip_id}",
                "nom_complet": "Jean Doe",
                "password": "motdepasse123",
                "sip_id": sip_id,
            },
        )
    ).json()


@pytest.mark.asyncio
async def test_check_balance_sans_secret_est_refuse(client: AsyncClient) -> None:
    # En-tete requis absent : FastAPI renvoie 422 avant meme d'entrer dans la dependance.
    reponse = await client.get("/api/check_balance", params={"sip_id": "1001"})
    assert reponse.status_code == 422


@pytest.mark.asyncio
async def test_check_balance_secret_invalide_est_refuse(client: AsyncClient) -> None:
    reponse = await client.get(
        "/api/check_balance", params={"sip_id": "1001"}, headers={"X-AMI-Secret": "mauvais_secret"}
    )
    assert reponse.status_code == 401


@pytest.mark.asyncio
async def test_check_balance_sip_id_inconnu_404(client: AsyncClient) -> None:
    reponse = await client.get("/api/check_balance", params={"sip_id": "9999"}, headers=HEADERS)
    assert reponse.status_code == 404


@pytest.mark.asyncio
async def test_check_balance_autorise_si_solde_suffisant(client: AsyncClient) -> None:
    utilisateur = await _creer_utilisateur(client)
    await client.post(f"/api/utilisateurs/{utilisateur['id']}/crediter", json={"montant": "50.00"})

    reponse = await client.get("/api/check_balance", params={"sip_id": "1001"}, headers=HEADERS)
    assert reponse.status_code == 200
    donnees = reponse.json()
    assert donnees["autorise"] is True
    assert donnees["solde"] == "50.00"
    assert donnees["utilisateur_id"] == utilisateur["id"]


@pytest.mark.asyncio
async def test_check_balance_refuse_si_solde_nul(client: AsyncClient) -> None:
    await _creer_utilisateur(client)

    reponse = await client.get("/api/check_balance", params={"sip_id": "1001"}, headers=HEADERS)
    assert reponse.status_code == 200
    assert reponse.json()["autorise"] is False


@pytest.mark.asyncio
async def test_end_call_debite_via_sip_id_et_plafonne_au_solde(client: AsyncClient) -> None:
    utilisateur = await _creer_utilisateur(client)
    await client.post(f"/api/utilisateurs/{utilisateur['id']}/crediter", json={"montant": "10.00"})

    # Duree x tarif (1/s) = 30 AR, mais le solde n'est que de 10 AR : plafonne a 10.
    reponse = await client.post(
        "/api/end_call",
        headers=HEADERS,
        json={"channel": "SIP/1001-1", "sip_id": "1001", "duree": 30, "destination": "0341234567"},
    )
    assert reponse.status_code == 200
    donnees = reponse.json()
    assert donnees["cout_facture"] == "10.00"
    assert donnees["solde_restant"] == "0.00"


@pytest.mark.asyncio
async def test_end_call_service_ivr_est_gratuit(client: AsyncClient) -> None:
    utilisateur = await _creer_utilisateur(client)
    await client.post(f"/api/utilisateurs/{utilisateur['id']}/crediter", json={"montant": "10.00"})
    await client.post(
        "/api/services-ivr",
        json={"nom": "Commercial", "code": "1001#", "type": "queue", "destination": "commercial_queue"},
    )

    reponse = await client.post(
        "/api/end_call",
        headers=HEADERS,
        json={"channel": "SIP/1001-1", "sip_id": "1001", "duree": 30, "destination": "1001#"},
    )
    assert reponse.status_code == 200
    donnees = reponse.json()
    assert donnees["cout_facture"] == "0"
    assert donnees["solde_restant"] == "10.00"


@pytest.mark.asyncio
async def test_end_call_conference_reste_facturee(client: AsyncClient) -> None:
    utilisateur = await _creer_utilisateur(client)
    await client.post(f"/api/utilisateurs/{utilisateur['id']}/crediter", json={"montant": "10.00"})
    await client.post(
        "/api/services-ivr",
        json={"nom": "Conference", "code": "1004*", "type": "conf", "destination": "1234"},
    )

    reponse = await client.post(
        "/api/end_call",
        headers=HEADERS,
        json={"channel": "SIP/1001-1", "sip_id": "1001", "duree": 30, "destination": "1004*"},
    )
    assert reponse.status_code == 200
    donnees = reponse.json()
    # Tout le menu IVR est gratuit (y compris le transfert vers un agent),
    # sauf la conference qui reste facturee -- plafonnee au solde de 10 AR.
    assert donnees["cout_facture"] == "10.00"
    assert donnees["solde_restant"] == "0.00"


@pytest.mark.asyncio
async def test_end_call_appel_interne_reste_facture(client: AsyncClient) -> None:
    utilisateur = await _creer_utilisateur(client)
    await client.post(f"/api/utilisateurs/{utilisateur['id']}/crediter", json={"montant": "10.00"})

    reponse = await client.post(
        "/api/end_call",
        headers=HEADERS,
        json={"channel": "SIP/1001-1", "sip_id": "1001", "duree": 5, "destination": "2002"},
    )
    assert reponse.json()["cout_facture"] == "5.0"


@pytest.mark.asyncio
async def test_end_call_recharge_700_est_gratuite(client: AsyncClient) -> None:
    utilisateur = await _creer_utilisateur(client)
    await client.post(f"/api/utilisateurs/{utilisateur['id']}/crediter", json={"montant": "10.00"})

    reponse = await client.post(
        "/api/end_call",
        headers=HEADERS,
        json={"channel": "SIP/1001-1", "sip_id": "1001", "duree": 3, "destination": "RECHARGE-700"},
    )
    assert reponse.json()["cout_facture"] == "0"
    assert reponse.json()["solde_restant"] == "10.00"


@pytest.mark.asyncio
async def test_end_call_consultation_solde_600_est_gratuite(client: AsyncClient) -> None:
    utilisateur = await _creer_utilisateur(client)
    await client.post(f"/api/utilisateurs/{utilisateur['id']}/crediter", json={"montant": "10.00"})

    reponse = await client.post(
        "/api/end_call",
        headers=HEADERS,
        json={"channel": "SIP/1001-1", "sip_id": "1001", "duree": 5, "destination": "SOLDE-600"},
    )
    assert reponse.json()["cout_facture"] == "0"
    assert reponse.json()["solde_restant"] == "10.00"


@pytest.mark.asyncio
async def test_end_call_sip_id_inconnu_404(client: AsyncClient) -> None:
    reponse = await client.post(
        "/api/end_call",
        headers=HEADERS,
        json={"channel": "SIP/x-1", "sip_id": "0000", "duree": 10, "destination": "0341234567"},
    )
    assert reponse.status_code == 404


@pytest.mark.asyncio
async def test_pjsip_export_sans_secret_est_refuse(client: AsyncClient) -> None:
    reponse = await client.get("/api/pjsip_export")
    assert reponse.status_code == 422


@pytest.mark.asyncio
async def test_pjsip_export_contient_les_utilisateurs_actifs_avec_sip(client: AsyncClient) -> None:
    await _creer_utilisateur(client, sip_id="1001")

    reponse = await client.get("/api/pjsip_export", headers=HEADERS)
    assert reponse.status_code == 200
    assert reponse.headers["content-type"].startswith("text/plain")

    corps = reponse.text
    assert "[1001](endpoint-template)" in corps
    assert "[1001](auth-template)" in corps
    assert "[1001](aor-template)" in corps
    assert "username = 1001" in corps
    assert 'callerid = "Jean Doe" <1001>' in corps
    assert "mailboxes = 1001@voip-billing" in corps


@pytest.mark.asyncio
async def test_pjsip_export_exclut_les_utilisateurs_sans_sip_id(client: AsyncClient) -> None:
    creation = await client.post(
        "/api/utilisateurs",
        json={"username": "sansip", "nom_complet": "Sans SIP", "password": "motdepasse123"},
    )
    # sip_id est attribue automatiquement a la creation : on l'efface explicitement.
    await client.put(f"/api/utilisateurs/{creation.json()['id']}", json={"sip_id": None})

    reponse = await client.get("/api/pjsip_export", headers=HEADERS)
    assert "sansip" not in reponse.text.lower()
    assert "endpoint-template" not in reponse.text


@pytest.mark.asyncio
async def test_pjsip_export_exclut_les_utilisateurs_suspendus(client: AsyncClient) -> None:
    utilisateur = await _creer_utilisateur(client, sip_id="1001")
    await client.put(f"/api/utilisateurs/{utilisateur['id']}", json={"statut": "suspendu"})

    reponse = await client.get("/api/pjsip_export", headers=HEADERS)
    assert "[1001]" not in reponse.text


@pytest.mark.asyncio
async def test_acheter_credit_genere_un_token_non_credite(client: AsyncClient) -> None:
    utilisateur = await _creer_utilisateur(client)

    reponse = await client.post(
        "/api/ivr/acheter_credit",
        headers=HEADERS,
        json={"sip_id": "1001", "montant": "500"},
    )
    assert reponse.status_code == 200
    donnees = reponse.json()
    assert len(donnees["code_token"]) == 12
    assert donnees["code_token"].isdigit()
    assert donnees["montant"] == "500.00"

    # Le solde n'est pas credite directement : il faut composer 700+CODE#.
    solde = await client.get(f"/api/utilisateurs/{utilisateur['id']}")
    assert solde.json()["solde"] == "0.00"

    # Le token genere doit fonctionner via le circuit normal de recharge.
    recharge = await client.post(
        "/api/recharge",
        headers=HEADERS,
        json={"sip_id": "1001", "token": donnees["code_token"]},
    )
    assert recharge.json()["succes"] is True
    assert recharge.json()["nouveau_solde"] == "500.00"


@pytest.mark.asyncio
async def test_acheter_credit_sip_id_inconnu_404(client: AsyncClient) -> None:
    reponse = await client.post(
        "/api/ivr/acheter_credit",
        headers=HEADERS,
        json={"sip_id": "0000", "montant": "500"},
    )
    assert reponse.status_code == 404


@pytest.mark.asyncio
async def test_acheter_credit_compte_suspendu_refuse(client: AsyncClient) -> None:
    utilisateur = await _creer_utilisateur(client)
    await client.put(f"/api/utilisateurs/{utilisateur['id']}", json={"statut": "suspendu"})

    reponse = await client.post(
        "/api/ivr/acheter_credit",
        headers=HEADERS,
        json={"sip_id": "1001", "montant": "500"},
    )
    assert reponse.status_code == 403


@pytest.mark.asyncio
async def test_pjsip_export_echappe_les_guillemets_du_nom(client: AsyncClient) -> None:
    await client.post(
        "/api/utilisateurs",
        json={
            "username": "user1001",
            "nom_complet": 'Jean "Le Malin" Doe',
            "password": "motdepasse123",
            "sip_id": "1001",
        },
    )

    reponse = await client.get("/api/pjsip_export", headers=HEADERS)
    # Aucun guillemet interne ne doit casser la ligne callerid.
    for ligne in reponse.text.splitlines():
        if ligne.startswith("callerid"):
            assert ligne.count('"') == 2
