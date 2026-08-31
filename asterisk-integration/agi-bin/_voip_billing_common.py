"""Utilitaires partages par les scripts AGI de facturation.

Volontairement sans dependance externe (urllib/json stdlib uniquement) : ces
scripts tournent avec le Python systeme d'Asterisk, ou pip n'est pas garanti.
"""

import json
import sys
import urllib.error
import urllib.request

CONFIG_PATH = "/etc/asterisk/voip-billing.conf"


def charger_config() -> dict[str, str]:
    config = {"timeout": "3"}
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            for ligne in f:
                ligne = ligne.strip()
                if not ligne or ligne.startswith("#") or "=" not in ligne:
                    continue
                cle, _, valeur = ligne.partition("=")
                config[cle.strip()] = valeur.strip()
    except OSError:
        pass
    return config


def lire_environnement_agi() -> dict[str, str]:
    """Lit les paires agi_cle: valeur envoyees par Asterisk sur stdin jusqu'a la ligne vide."""
    env: dict[str, str] = {}
    for ligne in sys.stdin:
        ligne = ligne.rstrip("\n")
        if ligne == "":
            break
        if ":" in ligne:
            cle, _, valeur = ligne.partition(":")
            env[cle.strip()] = valeur.strip()
    return env


def commande_agi(commande: str) -> str:
    """Envoie une commande AGI sur stdout et lit la reponse sur stdin."""
    sys.stdout.write(commande + "\n")
    sys.stdout.flush()
    return sys.stdin.readline().strip()


def verbose(message: str) -> None:
    commande_agi(f'VERBOSE "{message}" 1')


def set_variable(nom: str, valeur: str) -> None:
    commande_agi(f'SET VARIABLE {nom} "{valeur}"')


def appel_api(config: dict[str, str], methode: str, chemin: str, payload: dict | None = None) -> dict | None:
    """Appelle l'API backend. Retourne None (et journalise) en cas d'echec reseau/HTTP."""
    url = config["api_base"].rstrip("/") + chemin
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    requete = urllib.request.Request(
        url,
        data=data,
        method=methode,
        headers={
            "X-AMI-Secret": config["ami_endpoints_secret"],
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(requete, timeout=float(config.get("timeout", 3))) as reponse:
            return json.loads(reponse.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError) as exc:
        verbose(f"voip-billing: erreur appel API {chemin} : {exc}")
        return None
