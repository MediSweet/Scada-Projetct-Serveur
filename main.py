import logging
import os
import sys

from apscheduler.schedulers.background import BackgroundScheduler

from services.database_service.sqlServer_connector import connect_sqlserver, close_sqlserver_connection
from etatDeMachineNotifMain.etat_de_machine_notif import etat_de_machine_notif
from services.google_sheets_service.sheets_connector import get_gspread_client

from tableToSheetMain.tableToSheetMain import table_to_sheet_main

sys.path.append("C:/Users/HP/Documents/Pinku doc/Projet Python/scada/PythonProject")
 #
 # logging.basicConfig(
 #     level=logging.INFO,
 #     format="%(asctime)s - %(levelname)s - %(message)s",
 #     datefmt="%Y-%m-%d %H:%M:%S"
 # )

# Crée un dossier de logs si nécessaire
log_dir = "C:\\Users\\Administrateur\\PycharmProjects\\PythonProject\\dist\\logs"
os.makedirs(log_dir, exist_ok=True)

# Configure le logger
logging.basicConfig(
    filename=os.path.join(log_dir, "GetDataFromScada.log"),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
client = get_gspread_client()
def main():
    conn = connect_sqlserver()

    if conn is None:
        logging.error("⛔ Connexion MySQL échouée. Arrêt du script.")
        return

    table_to_sheet_main(conn,client)
    etat_de_machine_notif(conn,client)
    close_sqlserver_connection(conn)
def getClient():
    return client
if __name__ == "__main__":
    main()
    from services.scheduler_service.job_scheduler import start_scheduler

    """Démarre le scheduler APScheduler."""
    scheduler = BackgroundScheduler()
    start_scheduler(scheduler)
