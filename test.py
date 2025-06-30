import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import numpy as np
import re
from datetime import datetime, timedelta, time
from pathlib import Path
import warnings
import os


class PresenceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Système de Gestion des Présences")
        self.root.geometry("1000x800")

        # Variables
        self.planning_file = tk.StringVar()
        self.punch_log_file = tk.StringVar()
        self.marge_minutes = tk.IntVar(value=45)

        # Style
        style = ttk.Style()
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TLabel', background='#f0f0f0', font=('Arial', 10))
        style.configure('TButton', font=('Arial', 10))
        style.configure('Header.TLabel', font=('Arial', 12, 'bold'))

        # Main Frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        ttk.Label(main_frame, text="SYSTÈME DE GESTION DES PRÉSENCES",
                  style='Header.TLabel').grid(row=0, column=0, columnspan=3, pady=10)

        # File Selection
        ttk.Label(main_frame, text="Fichier Planning:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.planning_file, width=70).grid(row=1, column=1, padx=5)
        ttk.Button(main_frame, text="Parcourir", command=self.browse_planning).grid(row=1, column=2)

        ttk.Label(main_frame, text="Fichier Log des Badges:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.punch_log_file, width=70).grid(row=2, column=1, padx=5)
        ttk.Button(main_frame, text="Parcourir", command=self.browse_punch_log).grid(row=2, column=2)

        # Parameters
        ttk.Label(main_frame, text="Marge (minutes):").grid(row=3, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.marge_minutes, width=10).grid(row=3, column=1, sticky=tk.W, padx=5)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=20)

        ttk.Button(button_frame, text="Analyser les Présences", command=self.analyze_presence).pack(side=tk.LEFT,
                                                                                                    padx=10)
        ttk.Button(button_frame, text="Exporter le Rapport", command=self.export_report).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Statistiques et Filtres", command=self.show_stats).pack(side=tk.LEFT, padx=10)

        # Log Area
        ttk.Label(main_frame, text="Journal d'activité:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.log_text = tk.Text(main_frame, height=20, width=120, wrap=tk.WORD)
        self.log_text.grid(row=6, column=0, columnspan=3)

        scrollbar = ttk.Scrollbar(main_frame, command=self.log_text.yview)
        scrollbar.grid(row=6, column=3, sticky=tk.NS)
        self.log_text.config(yscrollcommand=scrollbar.set)

        # Status Bar
        self.status_var = tk.StringVar()
        self.status_var.set("Prêt")
        ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN).grid(
            row=7, column=0, columnspan=3, sticky=tk.EW, pady=10)

        # Data attributes
        self.result_df = None
        self.synthese_paie = None
        self.absents_df = None
        self.badges_non_traite_df = None

        # Désactiver les avertissements
        warnings.filterwarnings('ignore')

    def browse_planning(self):
        filename = filedialog.askopenfilename(title="Sélectionner le fichier Planning",
                                              filetypes=(("Excel files", "*.xlsx"), ("All files", "*.*")))
        if filename:
            self.planning_file.set(filename)
            self.log_message(f"Fichier Planning sélectionné: {filename}")

    def browse_punch_log(self):
        filename = filedialog.askopenfilename(title="Sélectionner le fichier Log des Badges",
                                              filetypes=(("Excel files", "*.xlsx"), ("All files", "*.*")))
        if filename:
            self.punch_log_file.set(filename)
            self.log_message(f"Fichier Log des Badges sélectionné: {filename}")

    def log_message(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.status_var.set(message)
        self.root.update()

    # ----------------------------------------------------------------------------------
    # Fonctions utilitaires intégrées
    # ----------------------------------------------------------------------------------
    def read_excel_any(self, path, **kw):
        """Lecture robuste des fichiers Excel avec gestion des formats variés"""
        try:
            return pd.read_excel(path, **kw)
        except Exception as e:
            raise RuntimeError(f"Erreur lecture {path}: {e}")

    def clean_group(self, val):
        """Nettoyage des noms de groupes avec regex améliorée"""
        if pd.isna(val): return "Surface"
        match = re.search(r"(?:Groupe|GROUPE)\s*([A-D])", val, re.IGNORECASE)
        return f"GROUPE {match.group(1).upper()}" if match else "Surface"

    def parse_time(self, t_str):
        if pd.isna(t_str) or str(t_str).strip() == '':
            return None
        for fmt in ("%H:%M:%S", "%H:%M"):
            try:
                return datetime.strptime(str(t_str).strip(), fmt).time()
            except ValueError:
                continue
        return None

    def extraire_groupe_ou_surface(self, val):
        val = str(val).strip()
        if val.lower() == 'surface':
            return "SURFACE"
        if val.lower().startswith("groupe"):
            if "," in val:
                val = val.split(",")[0].strip()
            return val.upper()
        return "SURFACE"

    def determine_status(self, points, start_t, end_t, date, planned_len):
        """Détermine le statut de présence avec gestion des cas spéciaux"""
        num_points = len(points)

        if num_points == 0:
            return "Absente ⛔"

        if num_points == 1:
            return "Présence incomplète ⚠️"

        # Calcul de la durée réelle avec gestion des shifts de nuit
        start_dt = datetime.combine(date, points[0])
        end_dt = datetime.combine(date, points[-1])

        if end_t < start_t and points[-1] < start_t:
            end_dt += timedelta(days=1)

        duration = end_dt - start_dt

        if duration >= planned_len - timedelta(minutes=self.marge_minutes.get()):  # marge en minute
            return "Présente ✅"
        else:
            return "Présence partielle 🟠"

    def calculate_real_duration(self, points, date, start_t, end_t):
        """Calcule la durée réelle travaillée avec gestion du dépassement minuit"""
        if len(points) < 2:
            return timedelta(0)

        start_dt = datetime.combine(date, points[0])
        end_dt = datetime.combine(date, points[-1])

        # Ajustement pour les shifts de nuit
        if end_t < start_t and points[-1] < start_t:
            end_dt += timedelta(days=1)

        return end_dt - start_dt

    def corriger_statut_nuit(self, row):
        if str(row["Shift"]).strip().lower() != "nuit":
            return row  # ne rien faire si ce n'est pas un shift de nuit

        ent = row["Entré"]
        out = row["Sorti"]
        dur = row["Durée"]
        date = row["Date"]

        if pd.isna(ent) or pd.isna(out) or pd.isna(dur):
            return row

        # Conversion HH:MM → timedelta
        try:
            h, m = map(int, str(dur).split(":"))
            duree_td = timedelta(hours=h, minutes=m)
        except:
            return row

        # Récupérer l'heure de début et fin réelle du planning pour ce jour-là
        plan_row = self.plan_index.get((date, row["Département"]))
        if plan_row is None or pd.isna(plan_row.get("Start")) or pd.isna(plan_row.get("End")):
            return row

        start_t = plan_row["Start"]
        end_t = plan_row["End"]

        # Recalcule planned_len
        if end_t < start_t:  # Shift de nuit
            planned_len = datetime.combine(date + timedelta(days=1), end_t) - datetime.combine(date, start_t)
        else:
            planned_len = datetime.combine(date, end_t) - datetime.combine(date, start_t)

        # Recalcule du statut avec la marge configurée
        if duree_td >= planned_len - timedelta(minutes=self.marge_minutes.get()):
            row["Statut"] = "Présente ✅"
        else:
            row["Statut"] = "Présence partielle 🟠"

        return row

    def calculer_ecart(self, row):
        d = row["Durée"]
        if pd.isna(d) or isinstance(d, str) and d.strip() == "":
            return ""

        try:
            h, m = map(int, str(d).split(":"))
            dur = timedelta(hours=h, minutes=m)

            # ➕ Cas spécial : tout Repos = Heures Sup
            if row["Statut"] == "Présence hors planning 🟣":
                return f"+{dur.seconds // 3600:02d}:{(dur.seconds % 3600) // 60:02d} ⬆️"

            if dur < timedelta(hours=7):
                miss = timedelta(hours=7) - dur
                return f"-{miss.seconds // 3600:02d}:{(miss.seconds % 3600) // 60:02d} 🔻"

            elif dur > timedelta(hours=9):
                sup = dur - timedelta(hours=8)
                return f"+{sup.seconds // 3600:02d}:{(sup.seconds % 3600) // 60:02d} ⏫"

            else:
                return ""

        except:
            return ""

    def nettoyer_duree_et_ecart(self, row):
        if row["Statut"] == "Présence incomplète ⚠️" or row["Durée"] == "00:00":
            row["Durée"] = ""
            row["Écart HS/HM"] = ""
        return row

    def format_delta(self, td):
        if isinstance(td, str): return td
        if pd.isna(td): return ""
        if isinstance(td, timedelta):
            total_minutes = int(td.total_seconds() // 60)
            h, m = divmod(total_minutes, 60)
            return f"{h:02d}:{m:02d}"
        return str(td)

    def get_shift_range(self, day, start_t, end_t):
        TOL_BEFORE = timedelta(hours=12)
        TOL_AFTER = timedelta(hours=12)

        start_dt = datetime.combine(day, start_t) - TOL_BEFORE  # 14:00 ⇒ 02:00
        if end_t < start_t:  # shift de nuit
            end_dt = datetime.combine(day + timedelta(days=1), end_t) + TOL_AFTER
        else:  # shift de jour
            end_dt = datetime.combine(day, end_t) + TOL_AFTER
        return start_dt, end_dt

    def fix_night_shift_row(self, row):
        """
        • Si Shift == 'Nuit' et que l'entrée est logiquement avant la sortie (inversé), on inverse.
        • On recalcule alors la durée correcte en tenant compte du passage minuit.
        """
        if str(row["Shift"]).strip().lower() != "nuit":
            return row

        ent = row["Entré"]
        out = row["Sorti"]

        if pd.isna(ent) or pd.isna(out):
            return row

        if isinstance(ent, pd.Timestamp): ent = ent.time()
        if isinstance(out, pd.Timestamp): out = out.time()

        if ent < out:
            ent, out = out, ent  # inversion

        if ent > out:
            dt_start = datetime.combine(row["Date"], ent)
            dt_end = datetime.combine(row["Date"] + timedelta(days=1), out)
            row["Durée"] = dt_end - dt_start

        row["Entré"] = ent
        row["Sorti"] = out
        return row

    def minutes_from_ecart(self, val):
        if isinstance(val, str) and val:
            sign = 1 if val.startswith('+') else -1
            h, m = map(int, val[1:6].split(':'))
            return sign * (h * 60 + m)
        return 0

    def format_duree_minutes(self, total_min):
        if pd.isna(total_min) or total_min == 0:
            return ""
        sign = "-" if total_min < 0 else "+"
        total_min = abs(int(total_min))
        h, m = divmod(total_min, 60)
        return f"{sign}{h:02d}:{m:02d}"

    def standardiser_groupe(self, val):
        val = str(val).strip()
        if val.lower() == 'surface':
            return "SURFACE"
        if val.lower().startswith("groupe"):
            if "," in val:
                val = val.split(",")[0].strip()
            return val.upper()
        return "SURFACE"

    # ----------------------------------------------------------------------------------
    # Méthode principale d'analyse
    # ----------------------------------------------------------------------------------
    def analyze_presence(self):
        if not self.planning_file.get() or not self.punch_log_file.get():
            messagebox.showerror("Erreur", "Veuillez sélectionner les fichiers Planning et Log des Badges")
            return

        try:
            self.log_message("Début de l'analyse des présences...")

            # 1) Lecture des fichiers
            self.log_message("Lecture du fichier Planning...")
            plan_df = self.read_excel_any(self.planning_file.get(), sheet_name='Planning')

            self.log_message("Lecture du fichier Log des badges...")
            logs_df = self.read_excel_any(self.punch_log_file.get())

            # 2) Prétraitement des données
            self.log_message("Prétraitement des données...")

            # Planning
            plan_df['Date'] = pd.to_datetime(plan_df['Date']).dt.date
            plan_df['Start'] = plan_df['Start'].apply(self.parse_time)
            plan_df['End'] = plan_df['End'].apply(self.parse_time)
            plan_df['Groupe'] = plan_df['Groupe'].apply(self.standardiser_groupe)

            # Logs
            logs_df.columns = logs_df.columns.str.strip()
            if "No." in logs_df.columns:
                logs_df = logs_df.rename(columns={"No.": "No"})

            logs_df['Department'] = logs_df['Department'].apply(self.extraire_groupe_ou_surface)
            logs_df['DateTime'] = pd.to_datetime(
                logs_df['Date/Time'],
                dayfirst=True,
                errors='coerce'
            )

            # Liste Employés auto
            employe_df = (logs_df[['No', 'Name', 'Department']]
                          .dropna(subset=['No'])
                          .rename(columns={'Department': 'Groupe'})
                          .drop_duplicates()
                          .reset_index(drop=True))

            # Création d'un index de planning optimisé
            self.plan_index = {(row.Date, row.Groupe): row for _, row in plan_df.iterrows()}

            # 3) Analyse des présences
            self.log_message("Analyse des pointages...")
            results = []
            badges_non_traite_list = []

            # Réduire le planning à la plage réelle des logs
            date_series = logs_df['DateTime'].dropna().dt.date
            date_min_log = date_series.min()
            date_max_log = date_series.max()

            plan_df_reduit = plan_df[(plan_df['Date'] >= date_min_log) & (plan_df['Date'] <= date_max_log)]

            for _, emp in employe_df.iterrows():
                emp_no = emp['No']
                emp_name = emp['Name']
                emp_groupe = emp['Groupe']

                # Pointages de l'employé
                emp_logs = logs_df[(logs_df['No'] == emp_no) & logs_df['DateTime'].notna()] \
                    .sort_values('DateTime').copy()

                # Dates planning (réduit) + dates pointage
                dates_planning = set(plan_df_reduit[plan_df_reduit['Groupe'] == emp_groupe]['Date'].unique())
                dates_pointage = set(emp_logs['DateTime'].dt.date.unique())
                dates_a_traiter = sorted(dates_planning.union(dates_pointage))

                for date in dates_a_traiter:
                    plan_row = self.plan_index.get((date, emp_groupe))

                    if plan_row is None:
                        # Cas : jour non planifié pour ce groupe → vérifier si badge
                        day_start = datetime.combine(date, time.min)
                        day_end = datetime.combine(date, time.max)
                        mask_nonplan = (emp_logs["DateTime"] >= day_start) & (emp_logs["DateTime"] <= day_end)
                        punches = emp_logs[mask_nonplan]
                        emp_logs = emp_logs.drop(punches.index)

                        if not punches.empty:
                            points = sorted(punches['DateTime'].dt.time.tolist())
                            duration = self.calculate_real_duration(points, date, points[0], points[-1])
                            results.append({
                                'Name': emp_name,
                                'No.': emp_no,
                                'Département': emp_groupe,
                                'Date': date,
                                'Shift': "Hors Planning",
                                'Statut': "Présence hors planning 🟣",
                                'Entré': points[0],
                                'Sorti': points[-1] if len(points) > 1 else None,
                                'Durée': duration
                            })
                        continue

                    if pd.isna(plan_row.get("Start")):
                        # Cas : Repos (shift existe mais vide)
                        day_start = datetime.combine(date, time.min)
                        day_end = datetime.combine(date, time.max)
                        mask_repos = (emp_logs["DateTime"] >= day_start) & (emp_logs["DateTime"] <= day_end)
                        punches = emp_logs[mask_repos]
                        emp_logs = emp_logs.drop(punches.index)

                        if not punches.empty:
                            points = sorted(punches['DateTime'].dt.time.tolist())
                            duration = self.calculate_real_duration(points, date, points[0], points[-1])
                            results.append({
                                'Name': emp_name,
                                'No.': emp_no,
                                'Département': emp_groupe,
                                'Date': date,
                                'Shift': "Repos",
                                'Statut': "Présence hors planning 🟣",
                                'Entré': points[0],
                                'Sorti': points[-1] if len(points) > 1 else None,
                                'Durée': duration
                            })
                        continue

                    # Cas normal : shift planifié
                    start_t, end_t = plan_row.Start, plan_row.End
                    start_dt, end_dt = self.get_shift_range(date, start_t, end_t)

                    mask = (emp_logs["DateTime"] >= start_dt) & (emp_logs["DateTime"] <= end_dt)
                    shift_punches = emp_logs[mask]
                    emp_logs = emp_logs.drop(shift_punches.index)

                    points = sorted(shift_punches['DateTime'].dt.time.tolist())

                    if end_t < start_t:  # Nuit
                        planned_len = datetime.combine(date + timedelta(days=1), end_t) - \
                                      datetime.combine(date, start_t)
                    else:
                        planned_len = datetime.combine(date, end_t) - \
                                      datetime.combine(date, start_t)

                    status = self.determine_status(points, start_t, end_t, date, planned_len)
                    duration = self.calculate_real_duration(points, date, start_t, end_t)

                    shift_type = plan_row.get("Shift", "")

                    results.append({
                        'Name': emp_name,
                        'No.': emp_no,
                        'Département': emp_groupe,
                        'Date': date,
                        'Shift': shift_type,
                        'Statut': status,
                        'Entré': points[0] if points else None,
                        'Sorti': points[-1] if len(points) > 1 else None,
                        'Durée': duration,
                        'Détail': ' | '.join(p.strftime('%H:%M:%S') for p in points)
                    })

                # Enregistrer les pointages non utilisés pour cet employé
                if not emp_logs.empty:
                    badges_non_traite_list.append(emp_logs.copy())

            # 4) Post-traitement des résultats
            self.log_message("Post-traitement des résultats...")

            # Création du DataFrame à partir des résultats collectés
            self.result_df = pd.DataFrame(results)

            # Correction des shifts de nuit
            self.result_df = self.result_df.apply(self.fix_night_shift_row, axis=1)

            # Formatage de la durée en HH:MM
            self.result_df["Durée"] = self.result_df["Durée"].apply(self.format_delta)

            # Correction des statuts des shifts de nuit
            self.result_df = self.result_df.apply(self.corriger_statut_nuit, axis=1)

            # Calcul de l'écart HS/HM
            self.result_df["Écart HS/HM"] = self.result_df.apply(self.calculer_ecart, axis=1)

            # Nettoyage : vider Durée et Écart pour les cas incomplets
            self.result_df = self.result_df.apply(self.nettoyer_duree_et_ecart, axis=1)

            # Réorganiser / conserver l'ordre des colonnes
            final_cols = ['Name', 'No.', 'Département', 'Date', 'Shift',
                          'Statut', 'Entré', 'Sorti', 'Durée', 'Écart HS/HM']
            self.result_df = self.result_df[final_cols]

            # Supprimer automatiquement la dernière date des résultats
            date_a_exclure = self.result_df['Date'].max()
            self.result_df = self.result_df[self.result_df['Date'] != date_a_exclure].copy()
            self.log_message(f"🧹 Lignes du {date_a_exclure} supprimées du rapport final (synthèse).")

            # Fusion des badges non traités
            if badges_non_traite_list:
                self.badges_non_traite_df = (
                    pd.concat(badges_non_traite_list)
                    .sort_values('DateTime')
                    .reset_index(drop=True)
                )
            else:
                self.badges_non_traite_df = pd.DataFrame(columns=logs_df.columns)

            # 5) Préparation de la synthèse pour la paie
            self.log_message("Préparation de la synthèse pour la paie...")

            # Tableau récapitulatif pour la paie
            pivot_statuts = (self.result_df
                             .pivot_table(index=['No.', 'Name', 'Département'],
                                          columns='Statut',
                                          values='Date',
                                          aggfunc='count',
                                          fill_value=0)
                             .reset_index())

            # Cumul des écarts (en minutes)
            ecarts_min = self.result_df.assign(EcartMin=self.result_df['Écart HS/HM'].apply(self.minutes_from_ecart))
            cumul_ecart = ecarts_min.groupby(['No.', 'Name', 'Département'], as_index=False)['EcartMin'].sum()

            # Ajout de la colonne HH:MM au DataFrame complet
            cumul_ecart['Solde Écart'] = cumul_ecart['EcartMin'].apply(self.format_duree_minutes)

            # Fusion finale
            self.synthese_paie = pivot_statuts.merge(
                cumul_ecart[['No.', 'Name', 'Département', 'Solde Écart']],
                on=['No.', 'Name', 'Département'],
                how='left'
            )

            # Liste des absents
            self.absents_df = self.result_df[self.result_df['Statut'] == 'Absente ⛔']

            # 6) Statistiques
            n_employes = len(employe_df)
            n_jours = (date_max_log - date_min_log).days + 1
            n_present = len(self.result_df[self.result_df['Statut'].str.contains('✅')])
            n_absent = len(self.absents_df)

            self.log_message(f"Analyse terminée pour {n_employes} employés sur {n_jours} jours")
            self.log_message(f"Présences: {n_present} | Absences: {n_absent}")

            messagebox.showinfo("Succès", "Analyse des présences terminée avec succès!")

        except Exception as e:
            messagebox.showerror("Erreur", f"Une erreur est survenue: {str(e)}")
            self.log_message(f"ERREUR: {str(e)}")
            import traceback
            traceback.print_exc()

    def export_report(self):
        if self.result_df is None:
            messagebox.showwarning("Avertissement", "Veuillez d'abord analyser les présences")
            return

        try:
            filename = filedialog.asksaveasfilename(
                title="Enregistrer le rapport",
                defaultextension=".xlsx",
                filetypes=(("Excel files", "*.xlsx"), ("All files", "*.*")))

            if filename:
                with pd.ExcelWriter(filename) as writer:
                    self.synthese_paie.to_excel(writer, sheet_name="Synthese", index=False)
                    self.result_df.to_excel(writer, sheet_name='Rapport Détaillé', index=False)
                    self.absents_df.to_excel(writer, sheet_name='Absents', index=False)

                    # Employés présents dans les logs mais absents du planning
                    employes_in_result = set(self.result_df['No.'].unique())
                    employes_in_planning = set(pd.read_excel(self.punch_log_file.get())['No'].unique())
                    liste_employes_hors_planning = self.result_df[
                        self.result_df['No.'].isin(employes_in_result - employes_in_planning)
                    ][['No.', 'Name']].drop_duplicates()
                    liste_employes_hors_planning.to_excel(writer, sheet_name="HorsPlanning", index=False)

                    if not self.badges_non_traite_df.empty:
                        self.badges_non_traite_df.to_excel(writer, sheet_name="Badges_non_traites", index=False)

                    # Groupes présents dans le planning mais sans aucun badge
                    plan_df = pd.read_excel(self.planning_file.get())
                    groupes_plan = set(plan_df['Groupe'].unique())
                    groupes_logs = set(self.result_df['Département'].unique())
                    groupes_sans_badges = pd.DataFrame(
                        sorted(list(groupes_plan - groupes_logs)), columns=['Groupe sans badge'])
                    groupes_sans_badges.to_excel(writer, sheet_name="GroupesSansBadges", index=False)

                self.log_message(f"Rapport exporté avec succès: {filename}")
                messagebox.showinfo("Succès", f"Rapport exporté:\n{filename}")

        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'export: {str(e)}")
            self.log_message(f"ERREUR export: {str(e)}")

    def show_stats(self):
        if self.synthese_paie is None:
            messagebox.showwarning("Avertissement", "Veuillez d'abord analyser les présences")
            return

        # Créer une nouvelle fenêtre pour les statistiques
        stats_window = tk.Toplevel(self.root)
        stats_window.title("Statistiques et Filtres Avancés")
        stats_window.geometry("1200x800")

        # Notebook pour plusieurs onglets
        notebook = ttk.Notebook(stats_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # ------------------------------------------------------------------
        # Onglet 1: Synthèse Paie (avec filtres)
        # ------------------------------------------------------------------
        synth_frame = ttk.Frame(notebook)
        notebook.add(synth_frame, text="Synthèse Paie")

        # Frame pour les filtres
        filter_frame = ttk.Frame(synth_frame)
        filter_frame.pack(fill=tk.X, padx=5, pady=5)

        # Dictionnaire pour stocker les variables des filtres
        self.synth_filter_vars = {}

        # Créer un filtre pour chaque colonne de synthese_paie
        for i, col in enumerate(self.synthese_paie.columns):
            ttk.Label(filter_frame, text=f"{col}:").grid(row=0, column=i, padx=5, pady=2)

            if len(self.synthese_paie[col].unique()) < 20:  # Peu de valeurs uniques
                unique_vals = ['(Tous)'] + sorted(self.synthese_paie[col].dropna().unique().tolist())
                self.synth_filter_vars[col] = tk.StringVar(value='(Tous)')
                cb = ttk.Combobox(filter_frame, textvariable=self.synth_filter_vars[col],
                                  values=unique_vals, width=15)
                cb.grid(row=1, column=i, padx=5, pady=2)
            else:
                self.synth_filter_vars[col] = tk.StringVar()
                ttk.Entry(filter_frame, textvariable=self.synth_filter_vars[col], width=15).grid(
                    row=1, column=i, padx=5, pady=2)

        # Boutons de contrôle
        control_frame = ttk.Frame(synth_frame)
        control_frame.pack(fill=tk.X, pady=5)

        ttk.Button(control_frame, text="Appliquer Filtres",
                   command=lambda: self.apply_synth_filters(synth_tree)).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Réinitialiser",
                   command=lambda: self.reset_synth_filters(synth_tree)).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Exporter",
                   command=lambda: self.export_filtered_data(synth_tree, "Synthèse Paie")).pack(side=tk.LEFT, padx=5)



        # Treeview pour afficher les résultats
        synth_tree = ttk.Treeview(synth_frame, columns=list(self.synthese_paie.columns), show="headings", height=15)

        # Configurer les colonnes
        for col in self.synthese_paie.columns:
            synth_tree.heading(col, text=col)
            synth_tree.column(col, width=100, anchor=tk.CENTER)

        # Ajouter les données initiales
        for _, row in self.synthese_paie.iterrows():
            synth_tree.insert("", tk.END, values=list(row))

        # Scrollbars
        tree_scroll_y = ttk.Scrollbar(synth_frame, orient="vertical", command=synth_tree.yview)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        synth_tree.configure(yscrollcommand=tree_scroll_y.set)

        tree_scroll_x = ttk.Scrollbar(synth_frame, orient="horizontal", command=synth_tree.xview)
        tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        synth_tree.configure(xscrollcommand=tree_scroll_x.set)

        synth_tree.pack(fill=tk.BOTH, expand=True)

        # Lier le double-clic à la fonction d'affichage des détails
        synth_tree.bind("<Double-1>", lambda event: self.show_employee_details(event, synth_tree, stats_window))

        # ------------------------------------------------------------------
        # Onglet 2: Liste des Absents (avec filtres)
        # ------------------------------------------------------------------
        if not self.absents_df.empty:
            absents_frame = ttk.Frame(notebook)
            notebook.add(absents_frame, text="Liste des Absents")

            # Frame pour les filtres
            abs_filter_frame = ttk.Frame(absents_frame)
            abs_filter_frame.pack(fill=tk.X, padx=5, pady=5)

            # Dictionnaire pour stocker les variables des filtres
            self.abs_filter_vars = {}

            # Créer un filtre pour chaque colonne de absents_df
            for i, col in enumerate(self.absents_df.columns):
                ttk.Label(abs_filter_frame, text=f"{col}:").grid(row=0, column=i, padx=5, pady=2)

                if len(self.absents_df[col].unique()) < 20:  # Peu de valeurs uniques
                    unique_vals = ['(Tous)'] + sorted(self.absents_df[col].dropna().unique().tolist())
                    self.abs_filter_vars[col] = tk.StringVar(value='(Tous)')
                    cb = ttk.Combobox(abs_filter_frame, textvariable=self.abs_filter_vars[col],
                                      values=unique_vals, width=15)
                    cb.grid(row=1, column=i, padx=5, pady=2)
                else:
                    self.abs_filter_vars[col] = tk.StringVar()
                    ttk.Entry(abs_filter_frame, textvariable=self.abs_filter_vars[col], width=15).grid(
                        row=1, column=i, padx=5, pady=2)

            # Boutons de contrôle
            abs_control_frame = ttk.Frame(absents_frame)
            abs_control_frame.pack(fill=tk.X, pady=5)

            ttk.Button(abs_control_frame, text="Appliquer Filtres",
                       command=lambda: self.apply_abs_filters(abs_tree)).pack(side=tk.LEFT, padx=5)
            ttk.Button(abs_control_frame, text="Réinitialiser",
                       command=lambda: self.reset_abs_filters(abs_tree)).pack(side=tk.LEFT, padx=5)
            ttk.Button(abs_control_frame, text="Exporter",
                       command=lambda: self.export_filtered_data(abs_tree, "Liste Absents")).pack(side=tk.LEFT, padx=5)

            # Treeview pour afficher les résultats
            abs_tree = ttk.Treeview(absents_frame, columns=list(self.absents_df.columns), show="headings", height=15)

            # Configurer les colonnes
            for col in self.absents_df.columns:
                abs_tree.heading(col, text=col)
                abs_tree.column(col, width=100, anchor=tk.CENTER)

            # Ajouter les données initiales
            for _, row in self.absents_df.iterrows():
                abs_tree.insert("", tk.END, values=list(row))

            # Scrollbars
            tree_scroll_y = ttk.Scrollbar(absents_frame, orient="vertical", command=abs_tree.yview)
            tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
            abs_tree.configure(yscrollcommand=tree_scroll_y.set)

            tree_scroll_x = ttk.Scrollbar(absents_frame, orient="horizontal", command=abs_tree.xview)
            tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
            abs_tree.configure(xscrollcommand=tree_scroll_x.set)

            abs_tree.pack(fill=tk.BOTH, expand=True)

        # ------------------------------------------------------------------
        # Onglet 3: Statistiques Globales
        # ------------------------------------------------------------------
        stats_frame = ttk.Frame(notebook)
        notebook.add(stats_frame, text="Statistiques")

        # Zone de texte pour les statistiques
        stats_text = tk.Text(stats_frame, wrap=tk.WORD, width=100, height=30)
        stats_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Générer les statistiques
        self.generate_stats_summary(stats_text)

    def apply_synth_filters(self, tree):
        filtered_df = self.synthese_paie.copy()

        for col, var in self.synth_filter_vars.items():
            filter_value = var.get()

            if filter_value and filter_value != '(Tous)':
                try:
                    filtered_df = filtered_df[
                        filtered_df[col].astype(str).str.contains(filter_value, case=False, na=False)]
                except:
                    continue

        self.update_filtered_tree(tree, filtered_df)

    def reset_synth_filters(self, tree):
        for var in self.synth_filter_vars.values():
            if isinstance(var, tk.StringVar):
                var.set('(Tous)')

        self.update_filtered_tree(tree, self.synthese_paie)

    def apply_abs_filters(self, tree):
        filtered_df = self.absents_df.copy()

        for col, var in self.abs_filter_vars.items():
            filter_value = var.get()

            if filter_value and filter_value != '(Tous)':
                try:
                    filtered_df = filtered_df[
                        filtered_df[col].astype(str).str.contains(filter_value, case=False, na=False)]
                except:
                    continue

        self.update_filtered_tree(tree, filtered_df)

    def reset_abs_filters(self, tree):
        for var in self.abs_filter_vars.values():
            if isinstance(var, tk.StringVar):
                var.set('(Tous)')

        self.update_filtered_tree(tree, self.absents_df)

    def update_filtered_tree(self, tree, df):
        for item in tree.get_children():
            tree.delete(item)

        for _, row in df.iterrows():
            tree.insert("", tk.END, values=list(row))

    def export_filtered_data(self, tree, sheet_name):
        items = tree.get_children()
        if not items:
            messagebox.showwarning("Avertissement", "Aucune donnée à exporter")
            return

        data = []
        for item in items:
            data.append(tree.item(item)['values'])

        # Récupérer les noms de colonnes originaux
        if sheet_name == "Synthèse Paie":
            cols = self.synthese_paie.columns
        else:
            cols = self.absents_df.columns

        filtered_df = pd.DataFrame(data, columns=cols)

        filename = filedialog.asksaveasfilename(
            title=f"Enregistrer la {sheet_name} filtrée",
            defaultextension=".xlsx",
            filetypes=(("Excel files", "*.xlsx"), ("All files", "*.*")))

        if filename:
            filtered_df.to_excel(filename, index=False)
            messagebox.showinfo("Succès", f"Données exportées vers {filename}")

    def generate_stats_summary(self, text_widget):
        """Génère un résumé statistique dans le widget texte"""
        if self.result_df is None:
            return

        text_widget.delete(1.0, tk.END)

        # Statistiques globales
        total_employes = len(self.result_df['No.'].unique())
        total_jours = len(self.result_df['Date'].unique())

        text_widget.insert(tk.END, "=== STATISTIQUES GLOBALES ===\n\n")
        text_widget.insert(tk.END, f"Nombre total d'employés: {total_employes}\n")
        text_widget.insert(tk.END, f"Période couverte: {total_jours} jours\n\n")

        # Répartition par statut
        text_widget.insert(tk.END, "=== RÉPARTITION PAR STATUT ===\n\n")
        statut_counts = self.result_df['Statut'].value_counts()
        for statut, count in statut_counts.items():
            text_widget.insert(tk.END, f"{statut}: {count} ({count / len(self.result_df) * 100:.1f}%)\n")

        # Répartition par département
        text_widget.insert(tk.END, "\n=== RÉPARTITION PAR DÉPARTEMENT ===\n\n")
        dept_counts = self.result_df['Département'].value_counts()
        for dept, count in dept_counts.items():
            text_widget.insert(tk.END, f"{dept}: {count} ({count / len(self.result_df) * 100:.1f}%)\n")

        # Employés avec le plus d'absences
        if 'Absente ⛔' in statut_counts:
            text_widget.insert(tk.END, "\n=== TOP 5 DES ABSENCES ===\n\n")
            absents = self.result_df[self.result_df['Statut'] == 'Absente ⛔']
            top_absents = absents['Name'].value_counts().head(5)
            for name, count in top_absents.items():
                text_widget.insert(tk.END, f"{name}: {count} absences\n")

    def show_employee_details(self, event, tree, stats_window):
        # Récupérer l'item sélectionné
        item = tree.selection()[0]
        values = tree.item(item, 'values')

        # Extraire le numéro et le nom de l'employé
        emp_no = values[0]
        emp_name = values[1]

        # Filtrer les données pour cet employé
        emp_data = self.result_df[self.result_df['No.'] == emp_no]

        # Créer une nouvelle fenêtre
        detail_window = tk.Toplevel(stats_window)
        detail_window.title(f"Détails de pointage - {emp_name} ({emp_no})")
        detail_window.geometry("1000x600")

        # Titre
        ttk.Label(detail_window, text=f"Détails de pointage pour {emp_name} ({emp_no})",
                  font=('Arial', 12, 'bold')).pack(pady=10)

        # Treeview pour afficher les détails
        columns = ['Date', 'Shift', 'Statut', 'Entré', 'Sorti', 'Durée', 'Écart HS/HM']
        tree = ttk.Treeview(detail_window, columns=columns, show="headings", height=20)

        # Configurer les colonnes
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120, anchor=tk.CENTER)

        # Ajouter les données
        for _, row in emp_data.iterrows():
            tree.insert("", tk.END, values=[
                row['Date'],
                row['Shift'],
                row['Statut'],
                row['Entré'] if not pd.isna(row['Entré']) else "",
                row['Sorti'] if not pd.isna(row['Sorti']) else "",
                row['Durée'],
                row['Écart HS/HM']
            ])

        # Scrollbars
        tree_scroll_y = ttk.Scrollbar(detail_window, orient="vertical", command=tree.yview)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        tree.configure(yscrollcommand=tree_scroll_y.set)

        tree_scroll_x = ttk.Scrollbar(detail_window, orient="horizontal", command=tree.xview)
        tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        tree.configure(xscrollcommand=tree_scroll_x.set)

        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Bouton d'export
        ttk.Button(detail_window, text="Exporter ces données",
                   command=lambda: self.export_employee_data(emp_data, emp_name, emp_no)).pack(pady=10)

    def export_employee_data(self, emp_data, emp_name, emp_no):
        filename = filedialog.asksaveasfilename(
            title=f"Exporter les données de {emp_name}",
            defaultextension=".xlsx",
            filetypes=(("Excel files", "*.xlsx"), ("All files", "*.*")),
            initialfile=f"Pointage_{emp_name}_{emp_no}.xlsx")

        if filename:
            emp_data.to_excel(filename, index=False)
            messagebox.showinfo("Succès", f"Données exportées vers {filename}")
            self.log_message(f"Export des données de {emp_name} ({emp_no}) vers {filename}")
if __name__ == "__main__":
    root = tk.Tk()
    app = PresenceApp(root)
    root.mainloop()