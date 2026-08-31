"""Actions AMI de haut niveau (construites au dessus de AMIClient.envoyer_action)."""

from app.infrastructure.ami.client import AMIClient


async def raccrocher_canal(client: AMIClient, channel: str, cause: str = "Normal Clearing") -> bool:
    """Coupe un appel en cours via l'action AMI Hangup."""
    reponse = await client.envoyer_action({"Action": "Hangup", "Channel": channel, "Cause": cause})
    return reponse.get("Response") == "Success"
