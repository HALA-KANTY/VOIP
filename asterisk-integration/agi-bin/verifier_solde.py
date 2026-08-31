#!/usr/bin/env python3
"""
AGI appele AVANT Dial() pour verifier le solde de l'appelant.

Positionne les variables de canal AUTORISE (0/1) et SOLDE, lues ensuite par
le dialplan pour decider d'autoriser l'appel ou de le refuser.

Echec reseau/API => fail-closed (AUTORISE=0) : mieux vaut refuser un appel
que facturer a l'aveugle si le backend est injoignable.

Usage dans extensions.conf : AGI(verifier_solde.py)
"""

import urllib.parse

from _voip_billing_common import charger_config, lire_environnement_agi, set_variable, appel_api, verbose


def main() -> None:
    config = charger_config()
    env = lire_environnement_agi()
    sip_id = env.get("agi_callerid", "")

    if not sip_id:
        verbose("voip-billing: agi_callerid absent, appel refuse")
        set_variable("AUTORISE", "0")
        return

    chemin = "/api/check_balance?" + urllib.parse.urlencode({"sip_id": sip_id})
    reponse = appel_api(config, "GET", chemin)

    if reponse is None:
        set_variable("AUTORISE", "0")
        return

    set_variable("AUTORISE", "1" if reponse.get("autorise") else "0")
    set_variable("SOLDE", str(reponse.get("solde", "0")))
    verbose(f"voip-billing: sip_id={sip_id} solde={reponse.get('solde')} autorise={reponse.get('autorise')}")


if __name__ == "__main__":
    main()
