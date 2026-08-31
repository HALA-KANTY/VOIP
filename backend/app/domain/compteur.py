"""Gestionnaire de compteurs temps reel, decouple de l'AMI et de la base de donnees
via des callbacks injectes (aucun import infrastructure ici)."""

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from decimal import Decimal

from app.domain.billing import calculer_cout, solde_suffisant

OnSoldeEpuise = Callable[[str, int], Awaitable[None]]
OnFinAppel = Callable[[str, int, int, Decimal], Awaitable[None]]


@dataclass
class CompteurActif:
    utilisateur_id: int
    solde_initial: Decimal
    tarif_par_seconde: Decimal
    secondes_ecoulees: int = 0
    task: asyncio.Task | None = field(default=None, repr=False)


class CompteurManager:
    """
    Pour chaque appel actif (identifie par channel_id) :
    - Un compteur incremente chaque seconde.
    - A chaque tick, on verifie si le solde couvre le cout deja engage.
    - Si le solde est epuise, on appelle `on_solde_epuise` (charge a l'appelant
      de couper l'appel via l'AMI).
    """

    def __init__(self, on_solde_epuise: OnSoldeEpuise, on_fin_appel: OnFinAppel) -> None:
        self._on_solde_epuise = on_solde_epuise
        self._on_fin_appel = on_fin_appel
        self.compteurs_actifs: dict[str, CompteurActif] = {}

    def demarrer_compteur(
        self, channel_id: str, utilisateur_id: int, solde: Decimal, tarif_par_seconde: Decimal
    ) -> None:
        if channel_id in self.compteurs_actifs:
            return
        compteur = CompteurActif(
            utilisateur_id=utilisateur_id, solde_initial=solde, tarif_par_seconde=tarif_par_seconde
        )
        compteur.task = asyncio.create_task(self._boucle_compteur(channel_id, compteur))
        self.compteurs_actifs[channel_id] = compteur

    async def _boucle_compteur(self, channel_id: str, compteur: CompteurActif) -> None:
        try:
            while True:
                await asyncio.sleep(1)
                compteur.secondes_ecoulees += 1
                cout_engage = calculer_cout(compteur.secondes_ecoulees, compteur.tarif_par_seconde)
                if not solde_suffisant(compteur.solde_initial, cout_engage):
                    await self._on_solde_epuise(channel_id, compteur.utilisateur_id)
                    return
        except asyncio.CancelledError:
            return

    async def arreter_compteur(self, channel_id: str) -> None:
        """Arrete le compteur et notifie `on_fin_appel` avec la duree/cout final."""
        compteur = self.compteurs_actifs.pop(channel_id, None)
        if compteur is None:
            return
        if compteur.task is not None and not compteur.task.done():
            compteur.task.cancel()
        cout_final = calculer_cout(compteur.secondes_ecoulees, compteur.tarif_par_seconde)
        await self._on_fin_appel(channel_id, compteur.utilisateur_id, compteur.secondes_ecoulees, cout_final)

    def est_actif(self, channel_id: str) -> bool:
        return channel_id in self.compteurs_actifs
