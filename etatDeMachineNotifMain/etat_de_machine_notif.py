import logging

import pandas as pd

from config.config import TABLES_Alarm
from etatDeMachineNotifMain.core.analyzer import analyze_machine_states
from etatDeMachineNotifMain.core.notifier import format_notification_message
from services.database_service.sqlServer_connector import get_data_from_db
from services.google_sheets_service.sheets_connector import connect_to_google_sheet
from services.google_sheets_service.sheets_operations import get_last_row_data, insert_data_into_sheet
from services.notification_service.ErrorNotification import envoyer_notification_google_chat
from tableToSheetMain.core.transform import transform_data


def etat_de_machine_notif(conn, client):
    for alias, table_name in TABLES_Alarm.items():
        try:
            logging.info(
                f"\n\n*************************************************************************************************\n"
                f"*******************************🚀 Traitement de {alias} *************************************\n"
                f"************************************************azerty*************************************************\n")

            sheet = connect_to_google_sheet(client, alias)
            old_row = get_last_row_data(sheet)

            if old_row.empty:
                logging.info("📅 Aucune donnée précédente détectée, récupération complète.")
                query = f"SELECT * FROM {table_name} ORDER BY TriggerTime DESC"
                new_data = get_data_from_db(query, conn)
            else:
                last_time_str = old_row['TriggerTime']
                last_time = pd.to_datetime(last_time_str).floor('s')
                sql_formatted_time = last_time.strftime('%Y-%m-%dT%H:%M:%S')
                query = f"SELECT * FROM {table_name} WHERE TriggerTime >= '{sql_formatted_time}' ORDER BY TriggerTime DESC"

                new_data = get_data_from_db(query, conn)

                # Convertir TriggerTime de new_data en datetime (sans millisecondes)
                new_data['TriggerTime'] = pd.to_datetime(new_data['TriggerTime']).dt.floor('s')

                # Filtrer new_data pour ne garder que les lignes après last_time
                new_data = new_data[new_data['TriggerTime'] > last_time]

            if new_data.empty:
                logging.info("📭 Aucune nouvelle donnée trouvée après filtrage.")
                continue
            else:
                analysis = analyze_machine_states(old_row, new_data)

                if analysis and analysis['status_changes']:
                    notification_message = format_notification_message(analysis)
                    envoyer_notification_google_chat(notification_message, 'changement')


                insert_data_into_sheet(sheet, new_data)
                logging.info(f"✅ Traitement terminé. {len(new_data)} nouvelles lignes ajoutées.")

        except Exception as e:
            logging.error(f"❌ Erreur critique: {str(e)}")
            envoyer_notification_google_chat(f"Erreur dans etat_de_machine_notif: {str(e)[:200]}")
            continue