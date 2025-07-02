import pandas as pd
import logging
from services.notification_service.ErrorNotification import envoyer_notification_google_chat


def transform_data(df, alias, olddate):
    """Transforme les données brutes SCADA en format de production instantanée pour Google Sheets."""
    logging.info("🔄 Début de la transformation des données...")

    try:
        if df is None or df.empty:
            logging.warning("⚠️ DataFrame d'entrée est vide !")
            return pd.DataFrame()

        # Vérifie la colonne TriggerTime
        if 'TriggerTime' not in df.columns:
            df['TriggerTime'] = pd.NaT

        # Colonnes machines
        machine_columns = [col for col in df.columns if col.startswith('cola_') or col.startswith('cold_')]
        if not machine_columns:
            msg = "⚠️ Aucune colonne machine trouvée !"
            logging.warning(msg)
            envoyer_notification_google_chat(msg)
            return pd.DataFrame()

        # Melt
        df_melted = pd.melt(
            df,
            id_vars='TriggerTime',
            value_vars=machine_columns,
            var_name='Machine',
            value_name='QteCumul'
        )

        df_melted['Machine'] = df_melted['Machine'].str.replace(r'^cola_', '', regex=True)
        df_melted['Machine'] = df_melted['Machine'].str.replace(r'^cold_', ' ', regex=True)
        # Convertir TriggerTime en datetime (arrondi seconde)
        df_melted['TriggerTime'] = pd.to_datetime(df_melted['TriggerTime']).dt.floor('s')

        # Tri
        df_melted.sort_values(['Machine', 'TriggerTime'], inplace=True, ignore_index=True)

        # Liste des alias où on veut utiliser la valeur brute plutôt que le diff
        TableDonnéeNonCumuler = ['Vitesse', ]

        if alias in TableDonnéeNonCumuler:
            df_melted['Qte'] = pd.to_numeric(df_melted['QteCumul'], errors='coerce').fillna(0)
        else:
            df_melted['Qte'] = df_melted.groupby('Machine', group_keys=False)['QteCumul'].diff()

            # Si sheet vide, garder la première ligne
            if olddate is None or str(olddate).startswith("1970"):
                first_idx = df_melted.groupby('Machine', sort=False).head(1).index
                df_melted.loc[first_idx, 'Qte'] = df_melted.loc[first_idx, 'QteCumul']

            # Gestion des reset compteur
            df_melted.loc[df_melted['Qte'] < 0, 'Qte'] = df_melted['QteCumul']

        # Supprimer la ligne déjà insérée (olddate)
        if olddate and not str(olddate).startswith("1970"):
            olddate_parsed = pd.to_datetime(olddate, errors='coerce').floor('s')
            df_melted = df_melted[df_melted['TriggerTime'] != olddate_parsed]

        # Nettoyage et finalisation
        df_final = df_melted[['TriggerTime', 'Machine', 'Qte']].drop_duplicates()
        return df_final.sort_values('TriggerTime', ascending=False, ignore_index=True)

    except Exception as e:
        logging.error(f"❌ Erreur transformation : {e}", exc_info=True)
        envoyer_notification_google_chat(f"❌ Erreur transformation : {e}")
        return pd.DataFrame()


def clean_data_for_sheets(df):
    """Remplace les NaN par des valeurs compatibles avec Google Sheets"""
    return df.fillna('')
