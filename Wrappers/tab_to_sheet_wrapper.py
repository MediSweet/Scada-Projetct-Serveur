from services.database_service.sqlServer_connector import connect_sqlserver, close_sqlserver_connection
from services.google_sheets_service.sheets_connector import get_gspread_client
from services.notification_service.ErrorNotification import envoyer_erreur_google_chat
from tableToSheetMain.tableToSheetMain import table_to_sheet_main


def tab_to_sheet_wrapper():
    """Wrapper pour fournir la connexion à la fonction principale."""
    conn = connect_sqlserver()
    if conn:
        try:
            client = get_gspread_client()
            table_to_sheet_main(conn,client)
        finally:
            close_sqlserver_connection(conn)
    else:
        envoyer_erreur_google_chat("⛔ Impossible d'établir la connexion SQL dans le scheduler.")
