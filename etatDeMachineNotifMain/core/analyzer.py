from collections import defaultdict

def group_machines_by_type(machine_name):
    if machine_name.startswith('cola_L'):
        return 'Ligne'          # Regroupement par type (Ligne)
    elif machine_name.startswith('cola_GM'):
        return 'Grande_Machine'
    elif machine_name.startswith('cola_M60g'):
        return 'Machine_Carton'
    elif machine_name.startswith('cola_F'):
        return 'Four'
    return 'Autre'

def groupe_by_ligne(machine_name):
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
    return 'Autre'

def analyze_machine_states(old_row, new_data):
    if old_row.empty or new_data.empty:
        return None

    new_row = new_data.iloc[0]
    status_changes = defaultdict(list)
    current_states = defaultdict(dict)

    for col in new_data.columns:
        if col.startswith(('cola_L', 'cola_GM', 'cola_M60g', 'cola_F')):
            old_val = int(old_row.get(col, 0))
            new_val = int(new_row[col])

            # Pour le groupement, on garde Ligne 1, Ligne 2, etc.
            machine_group = groupe_by_ligne(col) if col.startswith('cola_L') else group_machines_by_type(col)

            # Récupérer le nom machine, par exemple 'M3' dans 'cola_L5_M3'
            parts = col.split('_')
            if len(parts) >= 3:
                machine_name = parts[2]  # Ex : 'M3'
            else:
                machine_name = parts[-1]

            # machine_id clair et uniforme : "Ligne 5 - M3"
            machine_id = f"{machine_group} - {machine_name}"

            # Etat actuel
            current_states[machine_group][machine_id] = "Marche" if new_val == 1 else "Arrêt"

            # Détection changements
            if old_val == 0 and new_val == 1:
                status_changes[machine_group].append((machine_id, "démarrage"))
            elif old_val == 1 and new_val == 0:
                status_changes[machine_group].append((machine_id, "arrêt"))

    return {
        "status_changes": dict(status_changes),
        "current_states": dict(current_states)
    }
