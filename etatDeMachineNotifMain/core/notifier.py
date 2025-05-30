from collections import defaultdict

def categorize_machine_group(group_name):
    """Fusionne les groupes Ligne 1..6 en 'Lignes', garde les autres tels quels."""
    if group_name.startswith("Ligne"):
        return "Lignes"
    elif group_name == "Grande_Machine":
        return "Grandes Machines"
    elif group_name == "Machine_Carton":
        return "Machines à carton"
    elif group_name == "Four":
        return "Four"
    else:
        return group_name.replace('_', ' ')

def format_notification_message(analysis):
    if not analysis:
        return None

    messages = []
    summary = defaultdict(lambda: [0, 0])  # [running, total] par catégorie

    # ✅ Partie 1 : Affichage des changements
    for machine_group, changes in analysis['status_changes'].items():
        if not changes:
            continue

        message_lines = [f"⚠️ **Changements {machine_group.replace('_', ' ')}**"]
        for machine_id, change in changes:
            emoji = "🟢" if change == "démarrage" else "🔴"
            message_lines.append(f"{emoji} {machine_id}: {change}")

        stats = analysis['current_states'].get(machine_group, {})
        running = sum(1 for v in stats.values() if v == "Marche")
        total = len(stats)
        if total > 0:
            message_lines.append(f"\n📊 Etat actuel: {running}/{total} en marche ({running / total * 100:.1f}%)")

        messages.append("\n".join(message_lines))

    # ✅ Partie 2 : Résumé global basé sur current_states (pas status_changes)
    for group_name, states in analysis["current_states"].items():
        cat = categorize_machine_group(group_name)
        for state in states.values():
            summary[cat][1] += 1  # total
            if state == "Marche":
                summary[cat][0] += 1  # running

    # ✅ Partie 3 : Construction du résumé
    if summary:
        messages.append("\n✅ **Résumé global :**")
        for cat, (running, total) in summary.items():
            percent = (running / total * 100) if total else 0
            messages.append(f"📊 ***État toute les {cat}*** : {running}/{total} machines en marche ({percent:.1f}%)")

    return "\n\n".join(messages)

