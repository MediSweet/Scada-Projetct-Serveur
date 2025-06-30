import requests
import logging

# 💬 URLs des deux webhooks Google Chat
WEBHOOK_ERREUR = "https://chat.googleapis.com/v1/spaces/AAAAGswoso0/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=-MmHzjqohk6knNVIWblu1CB1ZqOSJeIKTjifWmmLlkU"
WEBHOOK_CHANGEMENT = "https://chat.googleapis.com/v1/spaces/AAQAwfXGUqY/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=lhTYjgBDdOJJo17jBXvDJc_NZz8ryBIGDLhhhtrh3zY"


def envoyer_notification_google_chat(message, type_message="erreur"):
    """Envoie une notification à Google Chat selon le type (erreur ou changement)."""

    if type_message == "erreur":
        url = WEBHOOK_ERREUR
        prefixe = "🚨 **Erreur détectée :**"
    elif type_message == "changement":
        url = WEBHOOK_CHANGEMENT
        prefixe = "🔄 **Changement détecté :**"
    else:
        logging.warning(f"⚠️ Type de message inconnu : {type_message}")
        return

    payload = {"text": f"{prefixe}\n{message}"}
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        logging.info(f"✅ Notification '{type_message}' envoyée avec succès à Google Chat.")
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Erreur lors de l'envoi '{type_message}' à Google Chat : {e}")
