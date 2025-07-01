import logging
import os
import sys

from apscheduler.schedulers.background import BackgroundScheduler

from services.database_service.sqlServer_connector import connect_sqlserver, close_sqlserver_connection
from etatDeMachineNotifMain.etat_de_machine_notif import etat_de_machine_notif
from services.google_sheets_service.sheets_connector import get_gspread_client

from tableToSheetMain.tableToSheetMain import table_to_sheet_main

sys.path.append("C:/Users/HP/Documents/Pinku doc/Projet Python/scada/PythonProject")


# Création des handlers
log_dir = "C:\\Users\\Administrateur\\PycharmProjects\\PythonProject\\dist\\logs"
os.makedirs(log_dir, exist_ok=True)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Handler fichier
file_handler = logging.FileHandler(os.path.join(log_dir, "GetDataFromScada.log"), encoding='utf-8')
file_handler.setLevel(logging.INFO)

# Handler console (stream)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

# 💡 Forcer l'encodage UTF-8 si possible
try:
    sys.stdout.reconfigure(encoding='utf-8')  # Disponible à partir de Python 3.7+
except Exception as e:
    # Pour les versions plus anciennes, on ne fait rien ou on affiche un avertissement
    pass

# Format des logs
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

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
