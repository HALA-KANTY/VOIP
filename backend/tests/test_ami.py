import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.infrastructure.ami.client import AMIClient


def _make_client() -> AMIClient:
    async def _on_event(event: dict) -> None:
        pass

    return AMIClient(host="localhost", port=5038, username="user", secret="secret", on_event=_on_event)


@pytest.mark.asyncio
async def test_lire_message_parse_les_paires_cle_valeur() -> None:
    client = _make_client()
    reader = asyncio.StreamReader()
    reader.feed_data(b"Event: Hangup\r\nChannel: SIP/1001-000001\r\nCause: 16\r\n\r\n")
    reader.feed_eof()
    client._reader = reader

    message = await client._lire_message()

    assert message == {"Event": "Hangup", "Channel": "SIP/1001-000001", "Cause": "16"}


@pytest.mark.asyncio
async def test_lire_message_retourne_none_si_flux_ferme() -> None:
    client = _make_client()
    reader = asyncio.StreamReader()
    reader.feed_eof()
    client._reader = reader

    assert await client._lire_message() is None


@pytest.mark.asyncio
async def test_envoyer_action_encode_le_protocole_ami_et_attend_la_reponse() -> None:
    client = _make_client()
    writer = MagicMock()
    writer.write = MagicMock()
    writer.drain = AsyncMock()
    client._writer = writer

    tache = asyncio.create_task(client.envoyer_action({"Action": "Hangup", "Channel": "SIP/1001-1"}))
    await asyncio.sleep(0.05)

    payload = writer.write.call_args[0][0].decode("utf-8")
    assert "Action: Hangup\r\n" in payload
    assert "Channel: SIP/1001-1\r\n" in payload
    assert "ActionID: " in payload
    assert payload.endswith("\r\n\r\n")

    action_id = next(iter(client._pending_responses))
    client._pending_responses[action_id].set_result({"Response": "Success", "ActionID": action_id})

    reponse = await tache
    assert reponse["Response"] == "Success"


@pytest.mark.asyncio
async def test_envoyer_action_sans_connexion_leve_erreur() -> None:
    client = _make_client()
    with pytest.raises(ConnectionError):
        await client.envoyer_action({"Action": "Ping"})


async def _serveur_ami_factice(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    """Simule un serveur Asterisk minimal : banniere, accepte le Login, envoie un Event."""
    writer.write(b"Asterisk Call Manager/2.10.6\r\n")
    await writer.drain()

    lignes = []
    while True:
        ligne = await reader.readline()
        if ligne in (b"\r\n", b"\n", b""):
            break
        lignes.append(ligne.decode())
    requete = {}
    for ligne in lignes:
        cle, _, valeur = ligne.partition(":")
        requete[cle.strip()] = valeur.strip()

    writer.write(f"Response: Success\r\nActionID: {requete.get('ActionID', '')}\r\n\r\n".encode())
    await writer.drain()

    writer.write(b"Event: Hangup\r\nChannel: SIP/1001-1\r\n\r\n")
    await writer.drain()

    await asyncio.sleep(1)
    writer.close()


@pytest.mark.asyncio
async def test_demarrer_se_connecte_et_traite_un_evenement_sur_un_vrai_serveur() -> None:
    """
    Test d'integration bout-en-bout (pas de mock) contre un vrai serveur TCP :
    couvre exactement le bug ou envoyer_action('Login') attendait une reponse
    que la boucle de lecture, demarree trop tard, ne lisait jamais
    (timeout silencieux de 10s malgre une authentification reussie cote serveur).
    """
    evenements: list[dict] = []

    async def on_event(event: dict) -> None:
        evenements.append(event)

    serveur = await asyncio.start_server(_serveur_ami_factice, "127.0.0.1", 0)
    port = serveur.sockets[0].getsockname()[1]

    client = AMIClient(host="127.0.0.1", port=port, username="user", secret="secret", on_event=on_event)
    async with serveur:
        await client.demarrer()
        try:
            for _ in range(50):
                if evenements:
                    break
                await asyncio.sleep(0.1)
        finally:
            await client.arreter()

    assert evenements == [{"Event": "Hangup", "Channel": "SIP/1001-1"}]
