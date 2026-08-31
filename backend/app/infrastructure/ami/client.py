"""Client AMI (Asterisk Manager Interface) en asyncio pur.

Implemente directement le protocole texte AMI (paires cle: valeur separees par
une ligne vide) plutot que de dependre d'une librairie tierce, pour garder un
controle total sur la reconnexion automatique et eviter tout appel bloquant
dans la boucle d'evenements FastAPI.
"""

import asyncio
import itertools
import logging
from collections.abc import Awaitable, Callable

logger = logging.getLogger("ami_client")

AMIMessage = dict[str, str]
EventHandler = Callable[[AMIMessage], Awaitable[None]]


class AMIClient:
    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        secret: str,
        on_event: EventHandler,
        reconnect_delay_seconds: float = 5.0,
    ) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._secret = secret
        self._on_event = on_event
        self._reconnect_delay = reconnect_delay_seconds

        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._action_id_counter = itertools.count(1)
        self._pending_responses: dict[str, asyncio.Future[AMIMessage]] = {}
        self._listen_task: asyncio.Task | None = None
        self._running = False

    @property
    def connecte(self) -> bool:
        return self._writer is not None and not self._writer.is_closing()

    async def demarrer(self) -> None:
        """Lance la boucle de connexion/reconnexion en arriere-plan."""
        self._running = True
        self._listen_task = asyncio.create_task(self._boucle_connexion())

    async def arreter(self) -> None:
        self._running = False
        if self._listen_task is not None:
            self._listen_task.cancel()
        if self._writer is not None:
            self._writer.close()

    async def _boucle_connexion(self) -> None:
        while self._running:
            try:
                await self._connecter_et_ecouter()
            except (ConnectionError, OSError, asyncio.IncompleteReadError) as exc:
                logger.warning(
                    "Connexion AMI perdue (%s: %s), nouvelle tentative dans %ss",
                    type(exc).__name__,
                    exc,
                    self._reconnect_delay,
                )
            except asyncio.CancelledError:
                return
            finally:
                self._writer = None
                self._reader = None
            if self._running:
                await asyncio.sleep(self._reconnect_delay)

    async def _connecter_et_ecouter(self) -> None:
        self._reader, self._writer = await asyncio.open_connection(self._host, self._port)
        await self._reader.readline()  # banniere AMI (ex: "Asterisk Call Manager/x.y.z")

        # La boucle d'ecoute doit tourner AVANT d'envoyer Login : c'est elle qui lit
        # et resout la reponse de l'action via son ActionID. Sans ca, envoyer_action
        # attend une reponse que personne ne lit jamais et expire au bout de 10s
        # (avec un TimeoutError() sans message, d'ou un log "Connexion perdue ()"
        # meme quand Asterisk repond correctement).
        tache_ecoute = asyncio.create_task(self._ecouter())
        try:
            reponse = await self.envoyer_action(
                {"Action": "Login", "Username": self._username, "Secret": self._secret}
            )
            if reponse.get("Response") != "Success":
                raise ConnectionError(f"Echec d'authentification AMI: {reponse}")
            logger.info("Connexion AMI etablie sur %s:%s", self._host, self._port)
            await tache_ecoute
        finally:
            if not tache_ecoute.done():
                tache_ecoute.cancel()

    async def _ecouter(self) -> None:
        assert self._reader is not None
        while True:
            message = await self._lire_message()
            if message is None:
                raise ConnectionError("Flux AMI ferme par le serveur")
            if "ActionID" in message and message["ActionID"] in self._pending_responses:
                future = self._pending_responses.pop(message["ActionID"])
                if not future.done():
                    future.set_result(message)
            elif "Event" in message:
                await self._on_event(message)

    async def _lire_message(self) -> AMIMessage | None:
        assert self._reader is not None
        lignes: list[str] = []
        while True:
            ligne = await self._reader.readline()
            if not ligne:
                return None
            decodee = ligne.decode("utf-8", errors="replace").rstrip("\r\n")
            if decodee == "":
                break
            lignes.append(decodee)
        message: AMIMessage = {}
        for ligne in lignes:
            if ":" in ligne:
                cle, _, valeur = ligne.partition(":")
                message[cle.strip()] = valeur.strip()
        return message

    async def envoyer_action(self, action: AMIMessage, timeout: float = 10.0) -> AMIMessage:
        if self._writer is None:
            raise ConnectionError("Client AMI non connecte")

        action_id = str(next(self._action_id_counter))
        action = {**action, "ActionID": action_id}

        future: asyncio.Future[AMIMessage] = asyncio.get_event_loop().create_future()
        self._pending_responses[action_id] = future

        payload = "".join(f"{cle}: {valeur}\r\n" for cle, valeur in action.items()) + "\r\n"
        self._writer.write(payload.encode("utf-8"))
        await self._writer.drain()

        try:
            return await asyncio.wait_for(future, timeout=timeout)
        finally:
            self._pending_responses.pop(action_id, None)
