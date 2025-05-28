import pyodbc
import pandas as pd
import logging
from services.notification_service.ErrorNotification import envoyer_erreur_google_chat
from config.config import SQLSERVER_CONFIG
from contextlib import closing


def connect_sqlserver():
    """Établit une connexion SQL Server avec gestion améliorée des erreurs."""
    try:
        logging.info("🔗 Connexion à SQL Server...")

        conn_str = (
            f"DRIVER={SQLSERVER_CONFIG['DRIVER']};"
            f"SERVER={SQLSERVER_CONFIG['SERVER']};"
            f"DATABASE={SQLSERVER_CONFIG['DATABASE']};"
            "Trusted_Connection=yes;"
            "Application Name=PythonApp;"  # Pour identification dans SQL Server
        )

        # Ajout d'un timeout de connexion
        conn = pyodbc.connect(conn_str, timeout=30)

        # Configuration supplémentaire pour une meilleure compatibilité
        conn.setdecoding(pyodbc.SQL_WCHAR, encoding='utf-8')
        conn.setencoding(encoding='utf-8')

        logging.info("✅ Connexion SQL Server établie avec succès")
        return conn

    except pyodbc.InterfaceError as e:
        logging.error(f"❌ Erreur d'interface SQL Server : {e}")
    except pyodbc.OperationalError as e:
        logging.error(f"❌ Erreur opérationnelle SQL Server : {e}")
    except Exception as e:
        logging.error(f"❌ Erreur inattendue de connexion SQL Server : {e}")

    envoyer_erreur_google_chat("❌ Échec de la connexion à SQL Server")
    return None


def get_data_from_db(query, conn):
    """Récupère les données depuis SQL Server avec gestion robuste."""
    if conn is None:
        logging.error("Connexion non initialisée")
        return pd.DataFrame()

    try:
        logging.info(f"📡 Exécution requête SQL : {query[:100]}...")  # Log partiel de la requête

        # Utilisation de closing pour garantir la fermeture du curseur
        with closing(conn.cursor()) as cursor:
            # Exécution avec timeout
            cursor.execute(query)

            # Récupération des noms de colonnes
            columns = [column[0] for column in cursor.description]

            # Récupération des données par lots pour les gros datasets
            batch_size = 1000
            rows = cursor.fetchmany(batch_size)
            data = []

            while rows:
                data.extend(rows)
                rows = cursor.fetchmany(batch_size)

            # Conversion en DataFrame avec gestion des types
            df = pd.DataFrame.from_records(data, columns=columns)

            # Conversion des colonnes datetime
            for col in df.columns:
                if df[col].dtype == object:
                    try:
                        df[col] = pd.to_datetime(df[col])
                    except (ValueError, TypeError):
                        pass

            logging.info(f"✅ Données récupérées ({len(df)} lignes)")
            return df

    except pyodbc.ProgrammingError as e:
        logging.error(f"❌ Erreur de syntaxe SQL : {e}")
    except pyodbc.DatabaseError as e:
        logging.error(f"❌ Erreur de base de données : {e}")
    except Exception as e:
        logging.error(f"❌ Erreur inattendue lors de la récupération : {e}")

    envoyer_erreur_google_chat("❌ Échec de la récupération des données")
    return pd.DataFrame()


# Fonction utilitaire pour fermer la connexion
def close_sqlserver_connection(conn):
    """Ferme proprement la connexion SQL Server."""
    if conn:
        try:
            conn.close()
            logging.info("🔌 Connexion SQL Server fermée")
        except Exception as e:
            logging.error(f"❌ Erreur lors de la fermeture : {e}")