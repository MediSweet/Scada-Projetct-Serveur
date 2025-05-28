import logging
import sys

from services.database_service.sqlServer_connector import connect_sqlserver, close_sqlserver_connection
from etatDeMachineNotifMain.etat_de_machine_notif import etat_de_machine_notif
from services.google_sheets_service.sheets_connector import get_gspread_client

from tableToSheetMain.tableToSheetMain import table_to_sheet_main

sys.path.append("C:/Users/HP/Documents/Pinku doc/Projet Python/scada/PythonProject")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def main():
    conn = connect_sqlserver()
    if conn is None:
        logging.error("⛔ Connexion MySQL échouée. Arrêt du script.")
        return
    client = get_gspread_client()
    table_to_sheet_main(conn,client)
    #etat_de_machine_notif(conn)
    close_sqlserver_connection(conn)

if __name__ == "__main__":
    main()
    from services.scheduler_service.job_scheduler import start_scheduler
    start_scheduler()
