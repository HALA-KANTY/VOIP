"""Logique de facturation pure : aucune dependance vers la base de donnees ou l'AMI."""

from decimal import Decimal


class SoldeInsuffisantError(Exception):
    pass


def calculer_cout(duree_secondes: int, tarif_par_seconde: Decimal) -> Decimal:
    if duree_secondes < 0:
        raise ValueError("La duree ne peut pas etre negative")
    return Decimal(duree_secondes) * tarif_par_seconde


def solde_suffisant(solde: Decimal, cout: Decimal) -> bool:
    return solde >= cout


def secondes_avant_epuisement(solde: Decimal, tarif_par_seconde: Decimal) -> int:
    """Nombre entier de secondes facturables restantes avant epuisement du solde."""
    if tarif_par_seconde <= 0:
        raise ValueError("Le tarif doit etre strictement positif")
    return int(solde / tarif_par_seconde)


def crediter(solde_actuel: Decimal, montant: Decimal) -> Decimal:
    if montant <= 0:
        raise ValueError("Le montant a crediter doit etre strictement positif")
    return solde_actuel + montant


def debiter(solde_actuel: Decimal, montant: Decimal) -> Decimal:
    if montant <= 0:
        raise ValueError("Le montant a debiter doit etre strictement positif")
    if not solde_suffisant(solde_actuel, montant):
        raise SoldeInsuffisantError("Solde insuffisant pour ce debit")
    return solde_actuel - montant
