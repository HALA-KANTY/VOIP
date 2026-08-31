#!/usr/bin/env python3
"""
AGI appelé pendant l'appel (extension 700) pour recharger le solde.
Transmet le token saisi via DTMF à l'API du backend.

Usage dans extensions.conf :
    AGI(recharger_solde.py,${TOKEN_SAISI})
"""

from _voip_billing_common import charger_config, lire_environnement_agi, commande_agi, appel_api, verbose


def main() -> None:
    config = charger_config()
    env = lire_environnement_agi()

    # Récupération du token transmis par l'argument du dialplan
    token = env.get("agi_arg_1", "").strip()
    # Nettoyer le token : garder uniquement les chiffres (au cas où # ou * est transmis)
    token = ''.join(c for c in token if c.isdigit())
    sip_id = env.get("agi_callerid", "")

    if not sip_id:
        verbose("voip-billing: recharger_solde sans sip_id (callerid absent), abandon")
        commande_agi('SET VARIABLE RECHARGE_STATUT "ERROR"')
        return

    if not token:
        verbose(f"voip-billing: aucun token fourni pour l'utilisateur {sip_id}")
        commande_agi('SET VARIABLE RECHARGE_STATUT "EMPTY"')
        return

    verbose(f"voip-billing: tentative de recharge pour {sip_id} avec le token {token}")

    # Envoi de la requête au backend
    reponse = appel_api(
        config,
        "POST",
        "/api/recharge",
        {
            "sip_id": sip_id,
            "token": token
        }
    )

    if reponse is None:
        verbose(f"voip-billing: échec de l'appel API de recharge pour {sip_id}")
        commande_agi('SET VARIABLE RECHARGE_STATUT "FAILED"')
    elif reponse.get("succes") or reponse.get("status") == "success":
        nouveau_solde = reponse.get("nouveau_solde", "inconnu")
        verbose(f"voip-billing: recharge réussie pour {sip_id}. Nouveau solde: {nouveau_solde}")
        commande_agi('SET VARIABLE RECHARGE_STATUT "SUCCESS"')
    else:
        erreur_msg = reponse.get("detail", "token invalide ou expiré")
        verbose(f"voip-billing: rejet de la recharge pour {sip_id} ({erreur_msg})")
        commande_agi('SET VARIABLE RECHARGE_STATUT "INVALID"')


if __name__ == "__main__":
    main()