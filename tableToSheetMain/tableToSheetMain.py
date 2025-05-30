import logging
import pandas as pd
from config.config import TABLES
from tableToSheetMain.core.transform import transform_data, clean_data_for_sheets
from services.database_service.sqlServer_connector import get_data_from_db
from services.notification_service.ErrorNotification import envoyer_erreur_google_chat
from services.google_sheets_service.sheets_operations import get_last_record_date
from services.google_sheets_service.sheets_operations import  insert_data_into_sheet
from services.google_sheets_service.sheets_connector import connect_to_google_sheet, get_gspread_client


def table_to_sheet_main(conn,client):

    for alias, table_name in TABLES.items():
        try:
            if alias != 'Etat':
                logging.info(f"\n\n*************************************************************************************************\n"
                             f"*******************************🚀 Traitement de {alias} *************************************\n"
                             f"*************************************************************************************************\n")

                sheet = connect_to_google_sheet(client,alias)
                if not sheet:
                    continue

                last_time = get_last_record_date(sheet)

                if last_time == pd.to_datetime('1970-01-01'):
                    logging.info("📅 Aucune donnée précédente détectée, récupération complète.")
                    query = f"SELECT * FROM {table_name}"
                    old_date = None
                else:
                    # Format the datetime for SQL Server
                    sql_formatted_time = last_time.strftime('%Y-%m-%dT%H:%M:%S')
                    query = f"SELECT * FROM {table_name} WHERE TriggerTime >= '{sql_formatted_time}'"
                    old_date = last_time

                new_data = get_data_from_db(query, conn)

                if new_data.empty or len(new_data)==1:
                    logging.info("📭 Aucune nouvelle donnée trouvée.")
                    continue

                if len(new_data)>1:
                    transformed_data = transform_data(new_data, alias, old_date)
                    cleaned_data = clean_data_for_sheets(transformed_data)
                    insert_data_into_sheet(sheet, cleaned_data, alias)

        except Exception as e:
            logging.error(f"❌ Erreur critique avec {alias}: {str(e)}", exc_info=True)
            continue