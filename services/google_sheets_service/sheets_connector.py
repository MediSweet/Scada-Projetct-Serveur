import gspread
from oauth2client.service_account import ServiceAccountCredentials
import logging
import config.config
from services.notification_service.ErrorNotification import envoyer_erreur_google_chat
def get_gspread_client():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(config.config.KEY_FILE, scope)
    return gspread.authorize(creds)

def connect_to_google_sheet(client, sheet_name):
    try:
        logging.info(f"🔄 Connexion Google Sheets : {sheet_name}")
        return client.open(sheet_name).worksheet(sheet_name)
    except Exception as e:
        logging.error(f"❌ Erreur connexion Google Sheets {sheet_name} : {e}")
        envoyer_erreur_google_chat(f"❌ Erreur connexion Google Sheets {sheet_name} : {e}")
        return None