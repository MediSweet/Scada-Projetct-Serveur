import logging
import pandas as pd
from services.notification_service.ErrorNotification import envoyer_erreur_google_chat

def get_last_row_data(sheet):
    """
    Récupère la dernière ligne non vide d'un Google Sheet et la retourne sous forme de Series pandas.

    Args:
        sheet: L'objet worksheet Google Sheets connecté.

    Returns:
        pd.Series: Une Series pandas contenant les données de la dernière ligne
                   ou une Series vide si le sheet est vide.
    """
    try:
        all_values = sheet.get_all_values()

        if not all_values or len(all_values) < 2:
            logging.info("Le sheet est vide ou ne contient que les en-têtes.")
            return pd.Series(dtype='object')

        headers = all_values[0]
        last_row_values = all_values[-1]

        # Associer les valeurs aux en-têtes
        last_row_dict = {
            header: last_row_values[i] if i < len(last_row_values) else None
            for i, header in enumerate(headers)
        }

        last_row_series = pd.Series(last_row_dict)

        # Conversion intelligente de TriggerTime si présent
        if 'TriggerTime' in last_row_series:
            last_row_series['TriggerTime'] = pd.to_datetime(
                last_row_series['TriggerTime'], dayfirst=True, errors='coerce'
            )

        # Conversion automatique des colonnes machine (0/1) si elles commencent par certains préfixes
        for col in last_row_series.index:
            if col.startswith(('cola_L', 'cola_MC', 'cola_GM', 'cola_F')):
                try:
                    last_row_series[col] = int(last_row_series[col])
                except (ValueError, TypeError):
                    last_row_series[col] = 0  # Valeur par défaut

        return last_row_series

    except Exception as e:
        logging.error(f"❌ Erreur lors de la récupération de la dernière ligne : {str(e)}", exc_info=True)
        return pd.Series(dtype='object')

def get_last_row_data_batch(sheet):
    """
    Récupère la dernière ligne de données via batch_get pour minimiser les appels API.
    Retourne une pd.Series représentant la dernière ligne.
    """
    try:
        col_a = sheet.col_values(1)
        last_row_index = len(col_a)

        if last_row_index <= 1:
            logging.info("Le sheet ne contient pas de données.")
            return pd.Series(dtype='object')

        # Récupère en-têtes et dernière ligne via batch_get
        ranges = [f'1:1', f'{last_row_index}:{last_row_index}']
        result = sheet.batch_get(ranges)

        headers = result[0][0] if result[0] else []
        last_row = result[1][0] if len(result) > 1 and result[1] else []

        # Associe les en-têtes aux valeurs
        row_dict = {
            header: last_row[i] if i < len(last_row) else None
            for i, header in enumerate(headers)
        }

        series = pd.Series(row_dict)

        # Conversion automatique de TriggerTime s'il existe
        if 'TriggerTime' in series:
            raw_trigger_time = series['TriggerTime']
            try:
                parsed_time = pd.to_datetime(raw_trigger_time, dayfirst=False, errors='coerce')
                series['TriggerTime'] = parsed_time
            except Exception as e:
                logging.warning(f"⚠️ Erreur de conversion de TriggerTime : {e}")
                series['TriggerTime'] = pd.NaT

        # Conversion automatique des colonnes machine (booléens/nombres)
        for col in series.index:
            if col.startswith(('cola_L', 'cola_MC', 'cola_GM', 'cola_F')):
                try:
                    series[col] = int(series[col])
                except (ValueError, TypeError):
                    series[col] = 0

        return series

    except Exception as e:
        logging.error(f"❌ Erreur critique dans get_last_row_data_batch : {str(e)}", exc_info=True)
        envoyer_erreur_google_chat(f"Erreur récupération dernière ligne : {e}")
        return pd.Series(dtype='object')


def get_last_record_date(sheet):
    """Récupère la dernière date enregistrée depuis la 1ère colonne de Google Sheets."""
    try:
        values = sheet.col_values(1)  # Récupère uniquement la 1ère colonne

        if not values or len(values) < 2:  # Vérifie si la liste est vide ou ne contient que l'en-tête
            return pd.to_datetime('1970-01-01')

        last_date_str = values[-1]  # Dernière valeur de la colonne

        # Try parsing with different formats
        formats = [
            '%Y-%m-%d %H:%M:%S.%f',  # Format with microseconds
            '%Y-%m-%d %H:%M:%S',  # Format without microseconds
            '%d/%m/%Y %H:%M:%S',  # French format with day first
            '%m/%d/%Y %H:%M:%S'  # US format with month first
        ]

        last_time = None
        for fmt in formats:
            try:
                last_time = pd.to_datetime(last_date_str, format=fmt, errors='raise')
                break
            except:
                continue

        if last_time is None:
            logging.warning(f"⚠️ Format de date non reconnu : {last_date_str}")
            return pd.to_datetime('1970-01-01')

        return last_time

    except Exception as e:
        logging.error(f"❌ Erreur récupération dernière ligne : {e}")
        envoyer_erreur_google_chat(f"Erreur récupération dernière ligne : {e}")
        return pd.to_datetime('1970-01-01')

# def insert_data_into_sheet(sheet, dataframe ):
#     """Insère les nouvelles données transformées dans Google Sheets."""
#     try:
#         if dataframe.empty:
#             logging.info("🟡 Aucune nouvelle donnée à insérer.")
#             return 0
#
#         dataframe['TriggerTime'] = dataframe['TriggerTime'].dt.strftime('%d/%m/%Y %H:%M:%S')
#         new_data = dataframe[[
#             'TriggerTime', 'cola_L1_M1', 'cola_L1_M2', 'cola_L1_M3', 'cola_L1_M4', 'cola_L1_M5',
#             'cola_L1_M6', 'cola_L1_M7', 'cola_L1_M8', 'cola_L1_M9', 'cola_L1_M10',
#             'cola_L2_M1', 'cola_L2_M2', 'cola_L2_M3', 'cola_L2_M4', 'cola_L2_M5',
#             'cola_L2_M6', 'cola_L2_M7', 'cola_L2_M8', 'cola_L2_M9', 'cola_L2_M10',
#             'cola_L3_M1', 'cola_L3_M2', 'cola_L3_M3', 'cola_L3_M4', 'cola_L3_M5',
#             'cola_L3_M6', 'cola_L3_M7', 'cola_L3_M8', 'cola_L3_M9', 'cola_L3_M10',
#             'cola_GM1', 'cola_GM2', 'cola_GM3', 'cola_GM4' ,
#             'cola_M60g_1', 'cola_M60g_2', 'cola_M60g_3', 'cola_M60g_4', 'cola_M60g_5', 'cola_M60g_6'
#         ]].values.tolist()
#         sheet.append_rows(new_data[::-1])
#
#         logging.info(f"✅ {len(new_data)} lignes insérées dans Google Sheets.")
#         return len(new_data)
#     except Exception as e:
#         logging.error(f"❌ Erreur insertion Google Sheets : {e}")
#         envoyer_erreur_google_chat(f"Erreur insertion données : {e}")
#         return 0

def insert_data_into_sheet(sheet, dataframe, tab_name=""):
    try:
        if dataframe.empty:
            logging.info(f"🟡 [{tab_name}] Aucune donnée à insérer.")
            return 0

        # if 'TriggerTime' in dataframe.columns:
        #     dataframe['TriggerTime'] = dataframe['TriggerTime'].dt.strftime('%d/%m/%Y %H:%M:%S')

        dataframe['TriggerTime'] = dataframe['TriggerTime'].astype(str)

        columns = dataframe.columns.tolist()  # Extrait automatiquement tous les headers

        new_data = dataframe[columns].values.tolist()
        sheet.append_rows(new_data[::-1])

        logging.info(f"✅ [{tab_name}] {len(new_data)} lignes insérées.")
        return len(new_data)

    except Exception as e:
        logging.error(f"❌ [{tab_name}] Erreur insertion : {e}")
        envoyer_erreur_google_chat(f"Erreur insertion {tab_name} : {e}")
        return 0

