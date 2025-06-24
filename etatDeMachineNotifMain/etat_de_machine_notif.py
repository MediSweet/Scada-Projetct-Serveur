import logging

import pandas as pd

from etatDeMachineNotifMain.core.analyzer import analyze_machine_states
from etatDeMachineNotifMain.core.notifier import format_notification_message
from services.database_service.sqlServer_connector import get_data_from_db
from services.google_sheets_service.sheets_connector import connect_to_google_sheet
from services.google_sheets_service.sheets_operations import get_last_row_data, insert_data_into_sheet
from services.notification_service.ErrorNotification import envoyer_erreur_google_chat


# def etat_de_machine_notif(conn,client):
#     try:
#         logging.info("🚀 Début du traitement de l'état des machines...")
#         sheet = connect_to_google_sheet(client,'Etat')
#         old_row = get_last_row_data(sheet)
#
#         if old_row.empty:
#             logging.info("📅 Aucune donnée précédente détectée, récupération complète.")
#             query = "SELECT * FROM DIV_etat ORDER BY TriggerTime DESC"
#         else:
#
#             last_time_str = old_row['TriggerTime']
#             query = f"""
#                 DECLARE @last_date datetime = CONVERT(datetime, '{last_time_str}', 120)
#                 SELECT * FROM DIV_etat
#                 WHERE TriggerTime > @last_date
#                 ORDER BY TriggerTime desc
#             """
#
#         new_data = get_data_from_db(query, conn)
#
#         if new_data.empty or len(new_data)==1:
#             logging.info("📭 Aucune nouvelle donnée trouvée.")
#             return
#
#
#
#         analysis = analyze_machine_states(old_row, new_data)
#
#         if analysis and analysis['status_changes']:
#             notification_message = format_notification_message(analysis)
#             envoyer_erreur_google_chat(notification_message)
#
#         insert_data_into_sheet(sheet, new_data)
#         logging.info(f"✅ Traitement terminé. {len(new_data)} nouvelles lignes ajoutées.")
#
#     except Exception as e:
#         logging.error(f"❌ Erreur critique: {str(e)}")
#         envoyer_erreur_google_chat(f"Erreur dans etat_de_machine_notif: {str(e)[:200]}")
#         raise

def etat_de_machine_notif(conn, client):
    try:
        logging.info(
            f"\n\n*************************************************************************************************\n"
            f"*******************************🚀 Traitement de Etat *************************************\n"
            f"*************************************************************************************************\n")

        sheet = connect_to_google_sheet(client, 'Etat')
        old_row = get_last_row_data(sheet)

        if old_row.empty:
            logging.info("📅 Aucune donnée précédente détectée, récupération complète.")
            query = "SELECT * FROM DIV_etat ORDER BY TriggerTime DESC"
            new_data = get_data_from_db(query, conn)
        else:
            last_time_str = old_row['TriggerTime']
            last_time = pd.to_datetime(last_time_str).floor('s')
            sql_formatted_time = last_time.strftime('%Y-%m-%dT%H:%M:%S')
            query = f"SELECT * FROM DIV_etat WHERE TriggerTime >= '{sql_formatted_time}' ORDER BY TriggerTime DESC"

            new_data = get_data_from_db(query, conn)

            # Convertir TriggerTime de new_data en datetime (sans millisecondes)
            new_data['TriggerTime'] = pd.to_datetime(new_data['TriggerTime']).dt.floor('s')

            # Filtrer new_data pour ne garder que les lignes après last_time
            new_data = new_data[new_data['TriggerTime'] > last_time]

        if new_data.empty:
            logging.info("📭 Aucune nouvelle donnée trouvée après filtrage.")
            return
        else:
            analysis = analyze_machine_states(old_row, new_data)

            if analysis and analysis['status_changes']:
                notification_message = format_notification_message(analysis)
                envoyer_erreur_google_chat(notification_message)

            insert_data_into_sheet(sheet, new_data)
            logging.info(f"✅ Traitement terminé. {len(new_data)} nouvelles lignes ajoutées.")

    except Exception as e:
        logging.error(f"❌ Erreur critique: {str(e)}")
        envoyer_erreur_google_chat(f"Erreur dans etat_de_machine_notif: {str(e)[:200]}")
        raise
