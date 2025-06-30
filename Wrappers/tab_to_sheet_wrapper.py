from etatDeMachineNotifMain.etat_de_machine_notif import etat_de_machine_notif
from main import getClient
from services.database_service.sqlServer_connector import connect_sqlserver, close_sqlserver_connection
from services.google_sheets_service.sheets_connector import get_gspread_client
from services.notification_service.ErrorNotification import envoyer_notification_google_chat
from tableToSheetMain.tableToSheetMain import table_to_sheet_main

client = getClient()
def tab_to_sheet_wrapper():
    """Wrapper pour fournir la connexion à la fonction principale."""
    conn = connect_sqlserver()
    if conn:
        try:

            table_to_sheet_main(conn,client)
        finally:
            close_sqlserver_connection(conn)
    else:
        envoyer_notification_google_chat("⛔ Impossible d'établir la connexion SQL dans le scheduler.")
def etat_machine_wrapper():
    """Wrapper pour exécuter la notification d'état de machine avec les connexions nécessaires."""
    conn = connect_sqlserver()
    if conn:
        try:

            etat_de_machine_notif(conn, client)
        finally:
            close_sqlserver_connection(conn)
    else:
        envoyer_notification_google_chat("⛔ Impossible d'établir la connexion SQL pour etat_machine_notif.")