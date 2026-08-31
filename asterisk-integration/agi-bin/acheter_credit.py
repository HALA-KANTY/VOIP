#!/usr/bin/env python3
"""
AGI appelé depuis le sous-menu IVR commercial (achat de crédit) pour générer
un token de recharge et le transmettre au dialplan pour lecture vocale.

Usage dans extensions.conf :
    AGI(acheter_credit.py,${EXTEN})   ; EXTEN = choix du montant (1 à 4)
"""

from _voip_billing_common import charger_config, lire_environnement_agi, appel_api, set_variable, verbose

MONTANTS = {"1": "500", "2": "1000", "3": "2000", "4": "5000"}


def main() -> None:
    config = charger_config()
    env = lire_environnement_agi()

    choix = env.get("agi_arg_1", "").strip()
    sip_id = env.get("agi_callerid", "")
    montant = MONTANTS.get(choix)

    if not sip_id or montant is None:
        verbose(f"voip-billing: achat credit invalide (sip_id={sip_id!r}, choix={choix!r})")
        set_variable("ACHAT_STATUT", "ERROR")
        return

    reponse = appel_api(config, "POST", "/api/ivr/acheter_credit", {"sip_id": sip_id, "montant": montant})

    if reponse is None or not reponse.get("code_token"):
        verbose(f"voip-billing: echec achat credit pour {sip_id}")
        set_variable("ACHAT_STATUT", "FAILED")
        return

    set_variable("CODE_TOKEN", reponse["code_token"])
    set_variable("ACHAT_STATUT", "SUCCESS")
    verbose(f"voip-billing: token genere pour {sip_id} (montant={montant})")


if __name__ == "__main__":
    main()
