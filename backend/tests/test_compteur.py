import asyncio
from decimal import Decimal

import pytest

from app.domain.compteur import CompteurManager


@pytest.mark.asyncio
async def test_arreter_compteur_appelle_on_fin_appel_avec_le_cout_final() -> None:
    appels_fin: list[tuple[str, int, int, Decimal]] = []

    async def on_solde_epuise(channel_id: str, utilisateur_id: int) -> None:
        pass

    async def on_fin_appel(channel_id: str, utilisateur_id: int, duree: int, cout: Decimal) -> None:
        appels_fin.append((channel_id, utilisateur_id, duree, cout))

    manager = CompteurManager(on_solde_epuise=on_solde_epuise, on_fin_appel=on_fin_appel)
    manager.demarrer_compteur("chan-1", utilisateur_id=42, solde=Decimal("100"), tarif_par_seconde=Decimal("1"))

    assert manager.est_actif("chan-1") is True
    await asyncio.sleep(1.2)
    await manager.arreter_compteur("chan-1")

    assert manager.est_actif("chan-1") is False
    assert len(appels_fin) == 1
    channel_id, utilisateur_id, duree, cout = appels_fin[0]
    assert channel_id == "chan-1"
    assert utilisateur_id == 42
    assert duree >= 1
    assert cout == Decimal(duree)


@pytest.mark.asyncio
async def test_solde_epuise_declenche_le_callback_et_arrete_le_compteur() -> None:
    epuises: list[str] = []

    async def on_solde_epuise(channel_id: str, utilisateur_id: int) -> None:
        epuises.append(channel_id)

    async def on_fin_appel(channel_id: str, utilisateur_id: int, duree: int, cout: Decimal) -> None:
        pass

    manager = CompteurManager(on_solde_epuise=on_solde_epuise, on_fin_appel=on_fin_appel)
    # Solde tres faible : epuise des la premiere seconde facturee.
    manager.demarrer_compteur("chan-2", utilisateur_id=1, solde=Decimal("0.5"), tarif_par_seconde=Decimal("1"))

    await asyncio.sleep(1.2)

    assert epuises == ["chan-2"]


def test_arreter_compteur_sur_channel_inconnu_ne_leve_pas_erreur() -> None:
    async def _noop(*args: object) -> None:
        pass

    manager = CompteurManager(on_solde_epuise=_noop, on_fin_appel=_noop)
    asyncio.run(manager.arreter_compteur("inconnu"))
