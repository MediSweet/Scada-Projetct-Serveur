from apscheduler.schedulers.background import BackgroundScheduler
import time
import logging

from Wrappers.tab_to_sheet_wrapper import tab_to_sheet_wrapper
from main import main
from services.notification_service.ErrorNotification import envoyer_erreur_google_chat
from tableToSheetMain.tableToSheetMain import table_to_sheet_main


def start_scheduler(scheduler):


    try:
        if not scheduler.get_job("tab_to_sheet_wrapper"):
            scheduler.add_job(tab_to_sheet_wrapper, 'interval', minutes=1, id="tab_to_sheet_wrapper" ) # ✅ passe une fonction SANS arguments
        scheduler.start()
        logging.info("✅ Scheduler démarré.")

        while True:
            time.sleep(300)

    except KeyboardInterrupt:
        scheduler.shutdown()
        logging.info("🛑 Scheduler arrêté par l'utilisateur.")
        envoyer_erreur_google_chat("🛑 Scheduler arrêté manuellement.")
    except Exception as e:
        logging.error(f"❌ Erreur dans le scheduler : {e}", exc_info=True)
        envoyer_erreur_google_chat(f"❌ Erreur dans le scheduler : {e}")
