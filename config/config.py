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
    "Quantité Jour": "DIV_jour",
    "Temps Perdu": "DIV_temp_prd"


}

TABLES_Alarm = {
    "Etat": "DIV_etat",
    "Ligne - alarme_synchron" : "DIV_alarme_synchron",
    "Ligne - alarme_sac_vide" : "DIV_alarme_sac_vide",
    "Ligne - alarme_photocellule" : "DIV_alarme_photocellule",
    "Ligne - alarme_joint_croise" : "DIV_alarme_joint_croise",
    "Ligne - alarme_film" : "DIV_alarme_film",
    "Ligne - alarme_err_encoder" : "DIV_alarme_err_encoder",
    "Ligne - alarme_arret_urgence" : "DIV_alarme_arret_urgence",
    "Ligne - alarme_chauff" : "DIV_alarme_chauff",
    "Ligne - Alarme_bariere_securite" : "DIV_Alarme_bariere_securite"
}
