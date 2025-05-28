import pandas as pd
import logging
from services.notification_service.ErrorNotification import envoyer_erreur_google_chat

def transform_data(df, alias, olddate):
    """Transforme les données brutes SCADA en format de production instantanée pour Google Sheets."""
    logging.info("🔄 Début de la transformation des données...")

    try:
        if df is None or df.empty:
            logging.warning("⚠️ DataFrame d'entrée est vide !")
            return pd.DataFrame()

        # S'assurer de la présence de TriggerTime
        if 'TriggerTime' not in df.columns:
            df['TriggerTime'] = pd.NaT
        else:
            df.rename(columns={'TriggerTime': 'TriggerTime'}, inplace=True)

        # Identifier les colonnes machines
        machine_columns = [col for col in df.columns if col.startswith('cola_')]
        if not machine_columns:
            msg = "⚠️ Aucune colonne machine trouvée !"
            logging.warning(msg)
            envoyer_erreur_google_chat(msg)
            return pd.DataFrame()

        # Melt + nettoyage
        df_melted = pd.melt(
            df,
            id_vars='TriggerTime',
            value_vars=machine_columns,
            var_name='Machine',
            value_name='QteCumul'
        )
        df_melted['Machine'] = df_melted['Machine'].str.replace('cola_', '', regex=False)

        # Tri efficace
        df_melted.sort_values(['Machine', 'TriggerTime'], inplace=True, ignore_index=True)

        if alias == 'Vitesse':


            qte_numeric = pd.to_numeric(df_melted['QteCumul'], errors='coerce')
            df_melted['Qte'] = qte_numeric.fillna(0)

        else:
            # Différence par machine
            df_melted['Qte'] = df_melted.groupby('Machine', group_keys=False)['QteCumul'].diff()

            # Si oldDate est vide ou "1970", on garde la première ligne de chaque machine avec QteCumul
            sheet_vide = olddate is None or str(olddate).startswith("1970")

            if sheet_vide:
                # Index des premières lignes de chaque machine
                first_idx = df_melted.groupby('Machine', sort=False).head(1).index
                df_melted.loc[first_idx, 'Qte'] = df_melted.loc[first_idx, 'QteCumul']

            # Reset → valeur négative
            df_melted.loc[df_melted['Qte'] < 0, 'Qte'] = df_melted['QteCumul']

        # Supprimer ligne correspondant à oldDate (si oldDate fourni et sheet pas vide)
        if olddate and not str(olddate).startswith("1970"):
            olddate_parsed = pd.to_datetime(olddate, errors='coerce')
            if not pd.isna(olddate_parsed):
                df_melted = df_melted[df_melted['TriggerTime'] != olddate_parsed]

        # Ajout des colonnes supplémentaires
        df_melted['Chef Quart'] = ' '
        df_melted['Opérateur'] = ' '

        # Réorganisation finale + retour
        df_final = df_melted[['TriggerTime', 'Machine', 'Chef Quart', 'Opérateur', 'Qte']]
        return df_final.sort_values('TriggerTime', ascending=False, ignore_index=True)

    except Exception as e:
        logging.error(f"❌ Erreur transformation : {e}", exc_info=True)
        envoyer_erreur_google_chat(f"❌ Erreur transformation : {e}")
        return pd.DataFrame()


# Dans votre fonction de transformation ou avant l'insertion
def clean_data_for_sheets(df):
    """Remplace les NaN par des valeurs compatibles avec Google Sheets"""
    return df.fillna('')  # Ou df.fillna(0) pour les nombres
