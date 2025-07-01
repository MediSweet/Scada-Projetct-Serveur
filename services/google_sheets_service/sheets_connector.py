import gspread
from oauth2client.service_account import ServiceAccountCredentials
import logging
import config.config
from time import sleep
import requests
from services.notification_service.ErrorNotification import envoyer_notification_google_chat


def get_gspread_client(max_retries=3, initial_timeout=30):
    """
    Crée et retourne un client Google Sheets avec gestion des erreurs et reconnexion

    Args:
        max_retries (int): Nombre maximal de tentatives de connexion
        initial_timeout (int): Timeout initial en secondes

    Returns:
        gspread.client.Client or None: Le client autorisé ou None en cas d'échec
    """
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']

    retry_count = 0
    while retry_count < max_retries:
        try:
            # Augmentation exponentielle du timeout
            timeout = initial_timeout * (retry_count + 1)

            logging.info(f"🔧 Tentative {retry_count + 1} de création du client Google Sheets (timeout: {timeout}s)")

            creds = ServiceAccountCredentials.from_json_keyfile_name(
                config.config.KEY_FILE, scope)

            # Création du client avec timeout configurable
            client = gspread.authorize(creds)

            # Test rapide de la connexion
            client.list_spreadsheet_files(limit=1)

            return client

        except requests.exceptions.Timeout as e:
            retry_count += 1
            if retry_count >= max_retries:
                logging.error(f"❌ Timeout persistant après {max_retries} tentatives")
                envoyer_notification_google_chat(
                    f"❌ Échec connexion Google Sheets: Timeout persistant après {max_retries} tentatives")
                return None

            wait_time = 5 * retry_count
            logging.warning(f"⌛ Timeout, nouvelle tentative dans {wait_time} sec...")
            sleep(wait_time)

        except Exception as e:
            logging.error(f"❌ Erreur inattendue lors de la création du client: {str(e)}")
            envoyer_notification_google_chat(
                f"❌ Erreur inattendue Google Sheets: {str(e)}")
            return None


def connect_to_google_sheet(client, sheet_name, max_retries=3):
    """
    Se connecte à une feuille spécifique avec gestion des erreurs

    Args:
        client: Client gspread autorisé
        sheet_name (str): Nom de la feuille
        max_retries (int): Nombre maximal de tentatives

    Returns:
        gspread.Worksheet or None: La feuille ou None en cas d'échec
    """
    retry_count = 0
    while retry_count < max_retries:
        try:
            logging.info(f"🔄 Tentative {retry_count + 1} de connexion à la feuille: {sheet_name}")
            sheet = client.open(sheet_name).worksheet(sheet_name)

            # Test rapide de la connexion
            sheet.get_all_records()

            return sheet

        except gspread.exceptions.APIError as e:
            if e.response.status_code == 429:
                # Trop de requêtes - on attend avant de réessayer
                wait_time = 60 * (retry_count + 1)
                logging.warning(f"⚠️ Quota dépassé, attente de {wait_time} sec...")
                sleep(wait_time)
                retry_count += 1
                continue
            else:
                logging.error(f"❌ Erreur API Google Sheets: {str(e)}")
                envoyer_notification_google_chat(
                    f"❌ Erreur API Google Sheets {sheet_name}: {str(e)}")
                return None

        except Exception as e:
            retry_count += 1
            if retry_count >= max_retries:
                logging.error(f"❌ Échec connexion à {sheet_name} après {max_retries} tentatives: {str(e)}")
                envoyer_notification_google_chat(
                    f"❌ Échec connexion Google Sheets {sheet_name}: {str(e)}")
                return None

            wait_time = 5 * retry_count
            logging.warning(f"⚠️ Erreur, nouvelle tentative dans {wait_time} sec...")
            sleep(wait_time)
