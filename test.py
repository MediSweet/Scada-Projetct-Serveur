import logging
from services.database_service.sqlServer_connector import get_data_from_db
from services.notification_service.ErrorNotification import envoyer_erreur_google_chat
from services.google_sheets_service.sheets_operations import get_last_row_data
from services.google_sheets_service.sheets_operations import insert_data_into_sheet
from services.google_sheets_service.sheets_connector import connect_to_google_sheets
from collections import defaultdict


def group_machines_by_type(machine_name):
    """Catégorise les machines par type"""
    if machine_name.startswith('cola_L'):
        return 'Ligne'
    elif machine_name.startswith('cola_GM'):
        return 'Grande_Machine'
    elif machine_name.startswith('cola_M60g'):
        return 'Machine_Carton'
    elif machine_name.startswith('cola_F'):
        return 'Four'
    else:
        return 'Autre'
def groupe_by_ligne(machine_name):
    """Catégorise les machines par type"""
    if machine_name.startswith('cola_L1'):
        return 'Ligne 1'
    elif machine_name.startswith('cola_L2'):
        return 'Ligne 2'
    elif machine_name.startswith('cola_L3'):
        return 'Ligne 3'
    elif machine_name.startswith('cola_L4'):
        return 'Ligne 4'
    elif machine_name.startswith('cola_L5'):
        return 'Ligne 5'
    elif machine_name.startswith('cola_L6'):
        return 'Ligne 6'
    else:
        return 'Autre'



def analyze_machine_states(old_row, new_data):
    """
    Analyse les changements d'état des machines entre l'ancienne ligne et la nouvelle plus récente.
    """
    if old_row.empty or new_data.empty:
        return None

    # Prendre la dernière ligne des nouvelles données (la plus récente)
    new_row = new_data.iloc[0]

    status_changes = defaultdict(list)
    current_states = defaultdict(dict)

    for col in new_data.columns:
        if col.startswith(('cola_L', 'cola_GM', 'cola_M60g', 'cola_F')):
            old_val = int(old_row.get(col, 0))
            new_val = int(new_row[col])

            # Regrouper par ligne (Ligne 1, Ligne 2...) ou autre
            machine_group = groupe_by_ligne(col) if col.startswith('cola_L') else group_machines_by_type(col)
            machine_name = col.split("_")[-1]  # e.g. M10
            machine_id = f"{machine_group} - {machine_name}"

            # État actuel
            current_states[machine_group][machine_id] = "Marche" if new_val == 1 else "Arrêt"

            # Détecter les changements
            if old_val == 0 and new_val == 1:
                status_changes[machine_group].append((machine_id, "démarrage"))
            elif old_val == 1 and new_val == 0:
                status_changes[machine_group].append((machine_id, "arrêt"))

    return {
        "status_changes": dict(status_changes),
        "current_states": dict(current_states)
    }

def format_notification_message(analysis):
    """Formate le message de notification par catégorie de machine"""
    if not analysis:
        return None

    messages = []

    # Parcourir par type de machine
    for machine_type, changes in analysis['status_changes'].items():
        if not changes:
            continue

        message_lines = [f"⚠️ **Changements {machine_type.replace('_', ' ')}**"]

        for machine, change in changes:
            short_name = machine.replace('cola_', '').replace('_', ' ')
            if change == "arrêt":
                message_lines.append(f"🔴 {short_name}: {change}")
            else :
                message_lines.append(f"🟢 {short_name}: {change}")
        # Ajouter le statut actuel
        stats = analysis['current_states'].get(machine_type, {})
        running = sum(1 for v in stats.values() if v == "Marche")
        total = len(stats)

        if total > 0:
            message_lines.append(f"\n📊 Etat actuel: {running}/{total} en marche ({running / total * 100:.1f}%)")

        messages.append("\n".join(message_lines))

    return "\n\n".join(messages)


def etat_de_machine_notif(conn):
    try:
        logging.info("🚀 Début du traitement de l'état des machines...")

        sheet = connect_to_google_sheets("Etat")

        # 1. Récupérer la dernière ligne complète du sheet
        old_row = get_last_row_data(sheet)

        if old_row.empty:
            logging.info("📅 Aucune donnée précédente détectée, récupération complète.")
            query = "SELECT * FROM DIV_etat ORDER BY TriggerTime DESC"
            last_time = None
        else:
            # 2. Extraire la date de la dernière ligne
            last_time_str  = old_row['TriggerTime']
            query = f"""
                        DECLARE @last_date datetime = CONVERT(datetime, '{last_time_str}', 120)
                        SELECT * FROM DIV_etat 
                        WHERE TriggerTime > @last_date
                        ORDER BY TriggerTime desc
                        """
        # 3. Récupérer les nouvelles données depuis la DB
        new_data = get_data_from_db(query, conn)

        if new_data.empty:
            logging.info("📭 Aucune nouvelle donnée trouvée.")
            return

        # 4. Analyser les changements
        analysis = analyze_machine_states(old_row, new_data)

        # 5. Envoyer les notifications
        if analysis and analysis['status_changes']:
            notification_message = format_notification_message(analysis)
            envoyer_erreur_google_chat(notification_message)

        # 6. Insérer les nouvelles données dans le sheet
        """header = [   # Toutes les colonnes machines
            'TriggerTime','cola_L1_M1',  'cola_L1_M2', 'cola_L1_M3', 'cola_L1_M4', 'cola_L1_M5',
            'cola_L1_M6', 'cola_L1_M7', 'cola_L1_M8', 'cola_L1_M9', 'cola_L1_M10',
            'cola_L2_M1', 'cola_L2_M2', 'cola_L2_M3', 'cola_L2_M4', 'cola_L2_M5',
            'cola_L2_M6', 'cola_L2_M7', 'cola_L2_M8', 'cola_L2_M9', 'cola_L2_M10',
            'cola_L3_M1', 'cola_L3_M2', 'cola_L3_M3', 'cola_L3_M4', 'cola_L3_M5',
            'cola_L3_M6', 'cola_L3_M7', 'cola_L3_M8', 'cola_L3_M9', 'cola_L3_M10',
            'cola_GM1', 'cola_GM2', 'cola_GM3', 'cola_GM4' ,
            'cola_M60g_1', 'cola_M60g_2', 'cola_M60g_3', 'cola_M60g_4', 'cola_M60g_5', 'cola_M60g_6'
        ]"""
        insert_data_into_sheet(sheet, new_data)

        logging.info(f"✅ Traitement terminé. {len(new_data)} nouvelles lignes ajoutées.")

    except Exception as e:
        logging.error(f"❌ Erreur critique: {str(e)}")
        envoyer_erreur_google_chat(f"Erreur dans etat_de_machine_notif: {str(e)[:200]}")
        raise