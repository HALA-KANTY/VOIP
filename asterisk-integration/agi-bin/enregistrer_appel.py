#!/usr/bin/env python3
"""
AGI appele a la fin de l'appel (extension `h`) pour enregistrer le CDR et
debiter le solde final via POST /api/end_call.

Les arguments sont fournis explicitement par le dialplan (plus fiable que de
les deduire des variables AGI) :

Usage dans extensions.conf :
    AGI(enregistrer_appel.py,${SIP_ID},${CDR(billsec)},${APPEL_DESTINATION},termine)

Ne doit jamais faire echouer le hangup : les erreurs sont journalisees, pas levees.
"""

from _voip_billing_common import charger_config, lire_environnement_agi, appel_api, verbose


def main() -> None:
    config = charger_config()
    env = lire_environnement_agi()

    sip_id = env.get("agi_arg_1", "")
    duree_str = env.get("agi_arg_2", "0")
    destination = env.get("agi_arg_3", "inconnue")
    statut = env.get("agi_arg_4", "termine")
    channel = env.get("agi_channel", "inconnu")

    if not sip_id:
        verbose("voip-billing: enregistrer_appel sans sip_id, abandon")
        return

    try:
        duree = int(duree_str)
    except ValueError:
        duree = 0

    reponse = appel_api(
        config,
        "POST",
        "/api/end_call",
        {
            "channel": channel,
            "sip_id": sip_id,
            "duree": duree,
            "destination": destination,
            "statut": statut,
        },
    )
    if reponse is None:
        verbose(f"voip-billing: echec enregistrement CDR pour {sip_id} ({channel})")
    else:
        verbose(f"voip-billing: CDR {reponse.get('cdr_id')} cout={reponse.get('cout_facture')}")


if __name__ == "__main__":
    main()
