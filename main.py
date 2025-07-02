import logging
import os
import sys

from apscheduler.schedulers.background import BackgroundScheduler

from services.database_service.sqlServer_connector import connect_sqlserver, close_sqlserver_connection
from etatDeMachineNotifMain.etat_de_machine_notif import etat_de_machine_notif
from services.google_sheets_service.sheets_connector import get_gspread_client

from tableToSheetMain.tableToSheetMain import table_to_sheet_main

sys.path.append("C:/Users/HP/Documents/Pinku doc/Projet Python/scada/PythonProject")


# Configuration du logger (à faire UNE SEULE FOIS au début de votre application)
log_dir = "C:\\Users\\Administrateur\\PycharmProjects\\PythonProject\\dist\\logs"
os.makedirs(log_dir, exist_ok=True)

# 1. Récupérer le logger principal
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 2. Supprimer tous les handlers existants pour éviter les duplications
logger.handlers.clear()

# 3. Créer les handlers (comme avant)
file_handler = logging.FileHandler(os.path.join(log_dir, "GetDataFromScada.log"), encoding='utf-8')
console_handler = logging.StreamHandler(sys.stdout)

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# 4. Ajouter les handlers
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# 5. Désactiver la propagation pour les loggers importés
logging.getLogger('apscheduler').propagate = False
logging.getLogger('googleapiclient').propagate = False


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
    scheduler = BackgroundScheduler({
        'apscheduler.jobstores.default': {
            'type': 'memory'
        },
        'apscheduler.executors.default': {
            'class': 'apscheduler.executors.pool:ThreadPoolExecutor',
            'max_workers': '1'
        }
    })
    start_scheduler(scheduler)
