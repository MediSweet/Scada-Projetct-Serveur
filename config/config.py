# 📄 config.py - Stocke les paramètres de connexion
KEY_FILE = "C:\\Users\\Administrateur\\PycharmProjects\\PythonProject\\key.json"

# MYSQL_CONFIG = {
#     "host": "localhost",
#     "user": "root",
#     "password": "medisec",
#     "database_service": "product"
# }
SQLSERVER_CONFIG = {
    'DRIVER': '{ODBC Driver 17 for SQL Server}',
    'SERVER': 'DESKTOP-9FO3EVN\\SQLEXPRESS',
    'DATABASE': 'product',
    # 'UID': 'utilisateur', a voir
    # 'PWD': 'motdepasse'

}

TABLES = {
    "Vitesse": "DIV_vitess",
    "Vide": "DIV_vide",
    "Synchronisation": "DIV_synch",
    # "Quantité Shift": "DIV_qte_sch",
    "Quantité Jour": "DIV_jour",
    "Etat": "DIV_etat",
    "Temps Perdu": "DIV_temp_prd"
}

