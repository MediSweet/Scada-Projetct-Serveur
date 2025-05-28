import requests
import logging


# 🔧  l'URL  du webhook Google Chat scada_Notification dans l'email de r&d
GOOGLE_CHAT_WEBHOOK_URL = "https://chat.googleapis.com/v1/spaces/AAAAGswoso0/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=-MmHzjqohk6knNVIWblu1CB1ZqOSJeIKTjifWmmLlkU"

def envoyer_erreur_google_chat(message):
    """Envoie une notification d'erreur à Google Chat via Webhook."""
    if not GOOGLE_CHAT_WEBHOOK_URL:
        logging.warning("⚠️ URL Webhook Google Chat non configurée.")
        return

    payload = {"text": f"🚨 **Erreur détectée :**\n{message}"}
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(GOOGLE_CHAT_WEBHOOK_URL, json=payload, headers=headers)
        response.raise_for_status()  # Lève une erreur si HTTP Status != 200

        logging.info("✅ Notification envoyée avec succès à Google Chat.")

    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Erreur lors de l'envoi à Google Chat : {e}")

