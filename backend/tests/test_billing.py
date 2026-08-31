from decimal import Decimal

import pytest

from app.domain.billing import (
    SoldeInsuffisantError,
    calculer_cout,
    crediter,
    debiter,
    secondes_avant_epuisement,
    solde_suffisant,
)


def test_calculer_cout_multiplie_duree_par_tarif() -> None:
    assert calculer_cout(60, Decimal("1.5")) == Decimal("90.0")


def test_calculer_cout_duree_negative_leve_erreur() -> None:
    with pytest.raises(ValueError):
        calculer_cout(-1, Decimal("1.0"))


def test_solde_suffisant() -> None:
    assert solde_suffisant(Decimal("10"), Decimal("10")) is True
    assert solde_suffisant(Decimal("9.99"), Decimal("10")) is False


def test_secondes_avant_epuisement() -> None:
    assert secondes_avant_epuisement(Decimal("100"), Decimal("2")) == 50


def test_crediter_augmente_le_solde() -> None:
    assert crediter(Decimal("10"), Decimal("5")) == Decimal("15")


def test_crediter_montant_negatif_leve_erreur() -> None:
    with pytest.raises(ValueError):
        crediter(Decimal("10"), Decimal("-1"))


def test_debiter_diminue_le_solde() -> None:
    assert debiter(Decimal("10"), Decimal("4")) == Decimal("6")


def test_debiter_solde_insuffisant_leve_erreur() -> None:
    with pytest.raises(SoldeInsuffisantError):
        debiter(Decimal("5"), Decimal("10"))
