def format_notification_message(analysis):
    if not analysis:
        return None

    messages = []
    for machine_type, changes in analysis['status_changes'].items():
        if not changes:
            continue

        message_lines = [f"⚠️ **Changements {machine_type.replace('_', ' ')}**"]
        for machine, change in changes:
            short_name = machine.replace('cola_', '').replace('_', ' ')
            emoji = "🟢" if change == "démarrage" else "🔴"
            message_lines.append(f"{emoji} {short_name}: {change}")

        stats = analysis['current_states'].get(machine_type, {})
        running = sum(1 for v in stats.values() if v == "Marche")
        total = len(stats)

        if total > 0:
            message_lines.append(f"\n📊 Etat actuel: {running}/{total} en marche ({running / total * 100:.1f}%)")

        messages.append("\n".join(message_lines))

    return "\n\n".join(messages)