# Importations nécessaires
import customtkinter as ctk # Pour l'interface graphique
import json # Pour la sauvegarde en JSON
import os # Pour vérifier l'existence des fichiers
from datetime import datetime # Pour la gestion des dates
from tkinter import messagebox # Pour les boîtes de dialogue d'alerte
import tkinter.ttk as ttk # Pour le widget Treeview (tableau)
from collections import defaultdict # Pour faciliter le comptage des dépenses
import io
import re # Importation pour extraire le montant numérique
import threading # Pour les appels API non bloquants

# Importation pour les requêtes API
import requests
import json

# Matériel pour le graphique camembert
import matplotlib
matplotlib.use("Agg") # Nécessaire pour la compatibilité avec tkinter
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image, ImageTk

# Classe principale de l'application
class BudgetApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Config de la fenêtre
        self.title("Suivi Budget Étudiant")
        self.geometry("1200x750")

        # Grille pour organiser les éléments
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Fichier de sauvegarde
        # Get the directory where the script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Define the data file path relative to the script directory
        self.data_file = os.path.join(script_dir, "budget_data.json")
        self.data = self.load_data() # Charge les données
        self.categories = self.load_categories() # Charge les catégories

        # Variables pour les filtres
        self.filter_month_var = ctk.StringVar(value="Tous")
        self.filter_category_var = ctk.StringVar(value="Toutes")
        
        # Pour le graphique
        self.analysis_chart_widget = None
        
        # Pour le chat IA
        self.openai_client = None
        self.chat_history_list = [] # Pour garder l'historique pour l'API

        # --- Le menu à gauche --- 
        self.sidebar_frame = ctk.CTkFrame(self, width=180, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Budget Tracker", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Les boutons du menu
        self.dashboard_button = ctk.CTkButton(self.sidebar_frame, text="Tableau de Bord", command=lambda: self.select_frame_by_name("dashboard"))
        self.dashboard_button.grid(row=1, column=0, padx=20, pady=10)
        self.transactions_button = ctk.CTkButton(self.sidebar_frame, text="Transactions", command=lambda: self.select_frame_by_name("transactions"))
        self.transactions_button.grid(row=2, column=0, padx=20, pady=10)
        self.analysis_button = ctk.CTkButton(self.sidebar_frame, text="Analyse", command=lambda: self.select_frame_by_name("analysis"))
        self.analysis_button.grid(row=3, column=0, padx=20, pady=10)
        self.chat_button = ctk.CTkButton(self.sidebar_frame, text="Chat IA", command=lambda: self.select_frame_by_name("chat"))
        self.chat_button.grid(row=4, column=0, padx=20, pady=10)

        # Choix du thème (clair/sombre)
        self.appearance_mode_label = ctk.CTkLabel(self.sidebar_frame, text="Mode d'Apparence:", anchor="w")
        self.appearance_mode_label.grid(row=6, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Light", "Dark", "System"],
                                                               command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=7, column=0, padx=20, pady=(10, 20))

        # --- Zone principale --- 
        self.dashboard_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.dashboard_frame.grid_columnconfigure(0, weight=1)
        self.transactions_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.transactions_frame.grid_columnconfigure(0, weight=1)
        self.transactions_frame.grid_rowconfigure(2, weight=1)
        self.analysis_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.analysis_frame.grid_columnconfigure(0, weight=1)
        self.analysis_frame.grid_columnconfigure(1, weight=2)
        self.analysis_frame.grid_rowconfigure(1, weight=1)
        self.chat_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.chat_frame.grid_columnconfigure(0, weight=1)
        self.chat_frame.grid_rowconfigure(1, weight=1) # L'historique prend l'espace

        # --- Création du contenu --- 
        self.create_dashboard_widgets()
        self.create_transactions_widgets()
        self.create_analysis_widgets()
        self.create_chat_widgets() # Création des widgets du chat

        # --- Initialisation --- 
        self.select_frame_by_name("dashboard") # Afficher le tableau de bord au démarrage
        self.appearance_mode_optionemenu.set("Dark") # Thème sombre par défaut
        self.update_category_dropdowns()
        self.update_month_filter_dropdown()
        self.update_transaction_list()

    # Charge les données depuis le fichier JSON
    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Assurer que les listes existent
                    if "income" not in data: data["income"] = []
                    if "expenses" not in data: data["expenses"] = []
                    # Vérifier et convertir les montants en float si nécessaire
                    for tx_type in ["income", "expenses"]:
                        for tx in data[tx_type]:
                            if isinstance(tx.get("amount"), str):
                                try: tx["amount"] = float(tx["amount"])
                                except ValueError: tx["amount"] = 0 # Mettre 0 si conversion impossible
                    return data
            except Exception as e:
                print(f"Erreur lors du chargement des données: {e}")
                messagebox.showerror("Erreur Chargement", f"Impossible de charger le fichier de données: {e}")
                return {"income": [], "expenses": []} # Retourner structure vide en cas d'erreur
        else:
            return {"income": [], "expenses": []} # Créer structure si fichier inexistant

    # Sauvegarde les données dans le fichier JSON
    def save_data(self):
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
        except IOError as e:
            messagebox.showerror("Erreur Sauvegarde", f"Impossible de sauvegarder les données: {e}")

    # Charge les catégories depuis les dépenses existantes et ajoute les catégories par défaut
    def load_categories(self):
        categories = set()
        if "expenses" in self.data:
            for expense in self.data["expenses"]:
                if "category" in expense: categories.add(expense["category"])
        default_categories = ["Alimentation", "Transport", "Loyer", "Factures", "Loisirs", "Autre"]
        categories.update(default_categories)
        return sorted(list(categories))
    
    # Ouvre une boîte de dialogue pour ajouter une nouvelle catégorie
    def add_category_dialog(self):
        dialog = ctk.CTkInputDialog(text="Entrez le nom de la nouvelle catégorie :", title="Ajouter Catégorie")
        new_category = dialog.get_input()
        if new_category:
            if self.add_category(new_category):
                messagebox.showinfo("Succès", f"Catégorie '{new_category}' ajoutée.")
            else:
                messagebox.showwarning("Attention", f"Catégorie '{new_category}' existe déjà ou est invalide.")

    # Ajoute une catégorie à la liste si elle est valide et n'existe pas déjà
    def add_category(self, category_name):
        category_name = category_name.strip()
        if category_name and category_name not in self.categories:
            self.categories.append(category_name)
            self.categories.sort()
            self.update_category_dropdowns()
            return True
        return False

    # Met à jour les listes déroulantes de catégories (ajout et filtre)
    def update_category_dropdowns(self):
        # Mise à jour de la combobox d'ajout de transaction
        if hasattr(self, 'expense_category_combobox'):
             self.expense_category_combobox.configure(values=self.categories)
             current_selection = self.expense_category_combobox.get()
             # Si la sélection actuelle n'est plus valide, choisir la première ou laisser vide
             if current_selection not in self.categories and self.categories:
                 self.expense_category_combobox.set(self.categories[0])
             elif not self.categories:
                 self.expense_category_combobox.set("")
        
        # Mise à jour de la combobox de filtre
        if hasattr(self, 'filter_category_combobox'):
            filter_categories = ["Toutes"] + self.categories
            self.filter_category_combobox.configure(values=filter_categories)
            current_filter_selection = self.filter_category_var.get()
            # Si la sélection actuelle n'est plus valide, choisir "Toutes"
            if current_filter_selection not in filter_categories:
                self.filter_category_var.set("Toutes")

    # Récupère la liste des mois uniques (format AAAA-MM) où des transactions existent
    def get_available_months(self):
        months = set()
        all_trans = self.data.get('income', []) + self.data.get('expenses', [])
        for item in all_trans:
            try:
                date_obj = datetime.strptime(item['date'], '%Y-%m-%d')
                months.add(date_obj.strftime('%Y-%m'))
            except (ValueError, KeyError): continue # Ignorer les dates invalides ou manquantes
        return sorted(list(months), reverse=True)

    # Met à jour la liste déroulante des mois pour le filtre
    def update_month_filter_dropdown(self):
        if hasattr(self, 'filter_month_combobox'):
            available_months = ["Tous"] + self.get_available_months()
            self.filter_month_combobox.configure(values=available_months)
            current_selection = self.filter_month_var.get()
            # Si la sélection actuelle n'est plus valide, choisir "Tous"
            if current_selection not in available_months:
                self.filter_month_var.set("Tous")

    # Change le cadre principal affiché (Tableau de bord, Transactions, etc.)
    def select_frame_by_name(self, name):
        buttons = {"dashboard": self.dashboard_button, "transactions": self.transactions_button, "analysis": self.analysis_button, "chat": self.chat_button}
        frames = {"dashboard": self.dashboard_frame, "transactions": self.transactions_frame, "analysis": self.analysis_frame, "chat": self.chat_frame}

        # Met en surbrillance le bouton du cadre sélectionné
        for btn_name, button in buttons.items():
            is_selected = (name == btn_name)
            # Utiliser les couleurs du thème actuel
            hover_color = ctk.ThemeManager.theme["CTkButton"]["hover_color"]
            default_color = ctk.ThemeManager.theme["CTkButton"]["fg_color"]
            button.configure(fg_color=hover_color if is_selected else default_color)

        # Affiche le cadre sélectionné et cache les autres
        for frame_name, frame in frames.items():
            if name == frame_name: frame.grid(row=0, column=1, sticky="nsew")
            else: frame.grid_forget()
        
        # Met à jour le contenu spécifique au cadre si nécessaire
        if name == "transactions":
            self.update_transaction_list()
            self.update_month_filter_dropdown()
            self.update_category_dropdowns()
        if name == "dashboard": self.update_dashboard()
        if name == "analysis": self.update_analysis()

    # Change le mode d'apparence (Light/Dark/System)
    def change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)
        self.style_treeview() # Met à jour le style du tableau
        self.update_analysis() # Redessine le graphique avec les nouvelles couleurs

    # Applique le style actuel au widget Treeview (tableau)
    def style_treeview(self):
        style = ttk.Style()
        theme = ctk.get_appearance_mode()
        # Obtenir les couleurs du thème CustomTkinter actuel
        fg_col = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["fg_color"])
        text_col = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkLabel"]["text_color"])
        select_col = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkButton"]["fg_color"])
        
        style.theme_use("default") # Utiliser le thème de base pour éviter les conflits
        # Configurer l'apparence générale du Treeview
        style.configure("Treeview", background=fg_col, foreground=text_col, fieldbackground=fg_col, borderwidth=0, rowheight=25)
        style.map('Treeview', background=[('selected', select_col)]) # Couleur de sélection
        # Configurer l'apparence des en-têtes
        style.configure("Treeview.Heading", background=fg_col, foreground=text_col, relief="flat", font=ctk.CTkFont(weight="bold"))
        style.map("Treeview.Heading", background=[('active', fg_col)]) # Couleur au survol de l'en-tête
        
        # Configurer les couleurs alternées des lignes si le Treeview existe
        if hasattr(self, 'transaction_tree'):
            odd_bg = fg_col # Couleur de fond pour lignes impaires
            # Essayer d'obtenir une couleur légèrement différente pour les lignes paires
            even_bg = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"].get("top_fg_color", fg_col))
            self.transaction_tree.tag_configure('oddrow', background=odd_bg, foreground=text_col)
            self.transaction_tree.tag_configure('evenrow', background=even_bg, foreground=text_col)

    # --- Création des widgets pour chaque écran --- 

    # Widgets du Tableau de Bord
    def create_dashboard_widgets(self):
        content_frame = ctk.CTkFrame(self.dashboard_frame)
        content_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        content_frame.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(content_frame, text="Aperçu du Tableau de Bord", font=ctk.CTkFont(size=24, weight="bold"))
        title_label.grid(row=0, column=0, columnspan=2, padx=20, pady=(10, 20), sticky="w")

        # Cadre pour le solde
        balance_frame = ctk.CTkFrame(content_frame)
        balance_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        balance_frame.grid_columnconfigure(0, weight=1)
        self.balance_label = ctk.CTkLabel(balance_frame, text="Solde Actuel: 0 FCFA", font=ctk.CTkFont(size=18))
        self.balance_label.grid(row=0, column=0, padx=15, pady=15, sticky="w")

        # Cadre pour les totaux Revenus/Dépenses
        summary_frame = ctk.CTkFrame(content_frame)
        summary_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        summary_frame.grid_columnconfigure((0,1), weight=1)
        self.total_income_label = ctk.CTkLabel(summary_frame, text="Revenu Total: 0 FCFA", font=ctk.CTkFont(size=14))
        self.total_income_label.grid(row=0, column=0, padx=15, pady=10, sticky="w")
        self.total_expenses_label = ctk.CTkLabel(summary_frame, text="Dépense Totale: 0 FCFA", font=ctk.CTkFont(size=14))
        self.total_expenses_label.grid(row=0, column=1, padx=15, pady=10, sticky="w")
        
        self.update_dashboard() # Mettre à jour les chiffres initiaux

    # Met à jour les indicateurs du Tableau de Bord (Solde, Total Revenus, Total Dépenses)
    def update_dashboard(self):
        total_income = sum(item.get('amount', 0) for item in self.data.get('income', []))
        total_expenses = sum(item.get('amount', 0) for item in self.data.get('expenses', []))
        balance = total_income - total_expenses
        # Fonction pour formater en FCFA (sans décimales, espace comme séparateur)
        fcfa_format = lambda x: f"{x:,.0f} FCFA".replace(',', ' ')
        self.balance_label.configure(text=f"Solde Actuel: {fcfa_format(balance)}")
        self.total_income_label.configure(text=f"Revenu Total: {fcfa_format(total_income)}")
        self.total_expenses_label.configure(text=f"Dépense Totale: {fcfa_format(total_expenses)}")

    # Widgets de l'écran Transactions
    def create_transactions_widgets(self):
        # --- Cadre pour ajouter une transaction --- 
        input_frame = ctk.CTkFrame(self.transactions_frame)
        input_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        input_frame.grid_columnconfigure(1, weight=1) # Le champ description prend plus de place

        # Type de transaction (Revenu/Dépense)
        self.transaction_type_var = ctk.StringVar(value="Dépense")
        ctk.CTkLabel(input_frame, text="Type:").grid(row=0, column=0, padx=(20, 5), pady=10, sticky="w")
        ctk.CTkSegmentedButton(input_frame, values=["Revenu", "Dépense"], variable=self.transaction_type_var, command=self.toggle_category_field).grid(row=0, column=1, columnspan=3, padx=5, pady=10, sticky="ew")

        # Description
        ctk.CTkLabel(input_frame, text="Description:").grid(row=1, column=0, padx=(20, 5), pady=5, sticky="w")
        self.desc_entry = ctk.CTkEntry(input_frame, placeholder_text="Ex: Café, Salaire")
        self.desc_entry.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky="ew")

        # Montant
        ctk.CTkLabel(input_frame, text="Montant (FCFA):").grid(row=2, column=0, padx=(20, 5), pady=5, sticky="w")
        self.amount_entry = ctk.CTkEntry(input_frame, placeholder_text="Ex: 500")
        self.amount_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        # Date
        ctk.CTkLabel(input_frame, text="Date (AAAA-MM-JJ):").grid(row=2, column=2, padx=(10, 5), pady=5, sticky="w")
        self.date_entry = ctk.CTkEntry(input_frame)
        self.date_entry.grid(row=2, column=3, padx=5, pady=5, sticky="ew")
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d")) # Pré-remplir avec date actuelle

        # Catégorie (visible seulement pour les dépenses)
        self.category_label = ctk.CTkLabel(input_frame, text="Catégorie:")
        self.expense_category_combobox = ctk.CTkComboBox(input_frame, values=self.categories)
        self.add_category_button = ctk.CTkButton(input_frame, text="+", width=30, command=self.add_category_dialog)
        # Placer les widgets de catégorie, seront cachés/montrés par toggle_category_field
        self.category_label.grid(row=3, column=0, padx=(20, 5), pady=5, sticky="w")
        self.expense_category_combobox.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        self.add_category_button.grid(row=3, column=2, padx=5, pady=5, sticky="w")
        self.toggle_category_field() # Appeler pour définir l'état initial

        # Bouton Ajouter
        ctk.CTkButton(input_frame, text="Ajouter Transaction", command=self.add_transaction).grid(row=4, column=0, columnspan=4, padx=20, pady=15, sticky="ew")

        # --- Cadre pour les filtres --- 
        filter_frame = ctk.CTkFrame(self.transactions_frame)
        filter_frame.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")
        filter_frame.grid_columnconfigure((1, 3), weight=1) # Les combobox prennent l'espace

        # Filtre par mois
        ctk.CTkLabel(filter_frame, text="Filtrer par Mois:").grid(row=0, column=0, padx=(20, 5), pady=10, sticky="w")
        self.filter_month_combobox = ctk.CTkComboBox(filter_frame, variable=self.filter_month_var, values=["Tous"] + self.get_available_months(), command=self.apply_filters)
        self.filter_month_combobox.grid(row=0, column=1, padx=5, pady=10, sticky="ew")

        # Filtre par catégorie
        ctk.CTkLabel(filter_frame, text="Filtrer par Catégorie:").grid(row=0, column=2, padx=(20, 5), pady=10, sticky="w")
        self.filter_category_combobox = ctk.CTkComboBox(filter_frame, variable=self.filter_category_var, values=["Toutes"] + self.categories, command=self.apply_filters)
        self.filter_category_combobox.grid(row=0, column=3, padx=(5, 20), pady=10, sticky="ew")

        # --- Le tableau des transactions et bouton supprimer --- 
        list_frame = ctk.CTkFrame(self.transactions_frame)
        list_frame.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="nsew") # Réduire pady bottom
        list_frame.grid_rowconfigure(0, weight=1) # Le Treeview prend l'espace vertical
        list_frame.grid_columnconfigure(0, weight=1) # Le Treeview prend l'espace horizontal

        # Création du Treeview (tableau)
        columns = ("type", "date", "description", "amount", "category")
        self.transaction_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        # Définition des en-têtes
        self.transaction_tree.heading("type", text="Type")
        self.transaction_tree.heading("date", text="Date")
        self.transaction_tree.heading("description", text="Description")
        self.transaction_tree.heading("amount", text="Montant")
        self.transaction_tree.heading("category", text="Catégorie")
        # Définition de la largeur et alignement des colonnes
        self.transaction_tree.column("type", width=80, anchor='center')
        self.transaction_tree.column("date", width=100, anchor='center')
        self.transaction_tree.column("description", width=350)
        self.transaction_tree.column("amount", width=120, anchor='e') # Aligné à droite
        self.transaction_tree.column("category", width=150, anchor='center')
        self.transaction_tree.grid(row=0, column=0, sticky="nsew")

        # Barre de défilement verticale pour le Treeview
        scrollbar = ctk.CTkScrollbar(list_frame, command=self.transaction_tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.transaction_tree.configure(yscrollcommand=scrollbar.set)
        self.style_treeview() # Appliquer le style

        # --- Bouton Supprimer --- 
        delete_button_frame = ctk.CTkFrame(self.transactions_frame, fg_color="transparent")
        delete_button_frame.grid(row=3, column=0, padx=20, pady=(5, 20), sticky="e") # Placé en bas à droite
        self.delete_button = ctk.CTkButton(delete_button_frame, text="Supprimer Sélection", command=self.delete_transaction, fg_color="#D32F2F", hover_color="#B71C1C")
        self.delete_button.grid(row=0, column=0)

    # Cache ou affiche le champ catégorie selon le type de transaction
    def toggle_category_field(self, *args):
        if self.transaction_type_var.get() == "Dépense":
            self.category_label.grid()
            self.expense_category_combobox.grid()
            self.add_category_button.grid()
        else:
            self.category_label.grid_remove()
            self.expense_category_combobox.grid_remove()
            self.add_category_button.grid_remove()

    # Ajoute une nouvelle transaction (revenu ou dépense)
    def add_transaction(self):
        trans_type = self.transaction_type_var.get()
        description = self.desc_entry.get().strip()
        amount_str = self.amount_entry.get().strip()
        date_str = self.date_entry.get().strip()
        category = self.expense_category_combobox.get() if trans_type == "Dépense" else None

        # Validation des entrées
        if not description:
            messagebox.showwarning("Entrée Invalide", "La description ne peut pas être vide.")
            return
        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError("Le montant doit être positif.")
        except ValueError:
            messagebox.showwarning("Entrée Invalide", "Veuillez entrer un montant numérique valide et positif.")
            return
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning("Entrée Invalide", "Format de date invalide. Utilisez AAAA-MM-JJ.")
            return
        if trans_type == "Dépense" and not category:
             if not self.categories:
                 messagebox.showwarning("Catégorie Manquante", "Veuillez d'abord ajouter une catégorie en utilisant le bouton '+'.")
             else:
                 messagebox.showwarning("Catégorie Manquante", "Veuillez sélectionner une catégorie pour la dépense.")
             return

        # Création du dictionnaire de la transaction
        transaction_data = {"description": description, "amount": amount, "date": date_str}
        if trans_type == "Dépense":
            transaction_data["category"] = category
            self.data["expenses"].append(transaction_data)
        else: # Revenu
            self.data["income"].append(transaction_data)

        self.save_data() # Sauvegarder les données
        # Mettre à jour l'interface
        self.update_transaction_list()
        self.update_dashboard()
        self.update_month_filter_dropdown()
        self.update_analysis()

        # Vider les champs d'entrée
        self.desc_entry.delete(0, ctk.END)
        self.amount_entry.delete(0, ctk.END)
        # Réinitialiser la catégorie si c'était une dépense
        if trans_type == "Dépense" and self.categories:
            self.expense_category_combobox.set(self.categories[0])

    # Supprime la ou les transactions sélectionnées dans le tableau
    def delete_transaction(self):
        selected_items = self.transaction_tree.selection()
        if not selected_items:
            messagebox.showwarning("Aucune Sélection", "Veuillez sélectionner une ou plusieurs transactions à supprimer.")
            return

        confirm = messagebox.askyesno("Confirmation", f"Êtes-vous sûr de vouloir supprimer {len(selected_items)} transaction(s) sélectionnée(s) ? Cette action est irréversible.")
        if not confirm:
            return

        items_to_delete_details = [] # Stocker les détails (type, index) des transactions à supprimer
        transactions_deleted = 0

        # Fonction pour comparer les transactions (tolérance pour float)
        def compare_transactions(tree_vals, data_tx):
            tree_type, tree_date, tree_desc, tree_amount_str, tree_cat = tree_vals
            # Extraire le montant numérique de la chaîne formatée
            amount_match = re.search(r'[\d\s,.]+', tree_amount_str.replace(' ', '').replace(',', '.'))
            if not amount_match: return False
            try:
                tree_amount = float(amount_match.group(0))
            except ValueError:
                return False
            
            data_type = "Dépense" if "category" in data_tx else "Revenu"
            data_cat = data_tx.get("category", "N/A")
            
            # Comparaison (attention aux floats)
            return (
                tree_type == data_type and
                tree_date == data_tx.get("date") and
                tree_desc == data_tx.get("description") and
                abs(tree_amount - data_tx.get("amount", 0.0)) < 0.001 and # Tolérance pour float
                tree_cat == data_cat
            )

        # Parcourir les éléments sélectionnés dans le Treeview pour identifier les transactions dans les données
        all_data_indices_to_delete = {'income': [], 'expenses': []}
        processed_tree_items = set()

        for item_id in selected_items:
            if item_id in processed_tree_items: continue # Eviter double traitement si sélection multiple identique
            values = self.transaction_tree.item(item_id, "values")
            trans_type = values[0]
            data_list_key = 'expenses' if trans_type == "Dépense" else 'income'
            data_list = self.data[data_list_key]
            found = False
            
            # Chercher l'index correspondant dans la liste de données
            for i, transaction in enumerate(data_list):
                 # Vérifier si cette transaction n'est pas déjà marquée pour suppression
                 # et si elle correspond aux valeurs du Treeview
                 if i not in all_data_indices_to_delete[data_list_key] and compare_transactions(values, transaction):
                    all_data_indices_to_delete[data_list_key].append(i)
                    processed_tree_items.add(item_id)
                    found = True
                    break # Passer à l'élément sélectionné suivant
            
            if not found:
                 print(f"Avertissement: Transaction non trouvée dans les données pour {values}")

        # Supprimer les transactions des données en commençant par la fin pour éviter les problèmes d'index
        for data_key, indices in all_data_indices_to_delete.items():
            if indices:
                indices.sort(reverse=True)
                data_list_to_modify = self.data[data_key]
                for index in indices:
                    if 0 <= index < len(data_list_to_modify):
                        del data_list_to_modify[index]
                        transactions_deleted += 1
                    else:
                        print(f"Erreur: Index {index} hors limites pour la suppression dans {data_key}.")

        if transactions_deleted > 0:
            self.save_data() # Sauvegarder les changements
            # Mettre à jour l'interface
            self.update_transaction_list()
            self.update_dashboard()
            self.update_analysis()
            messagebox.showinfo("Succès", f"{transactions_deleted} transaction(s) supprimée(s).")
        elif not processed_tree_items and selected_items: # Si on a sélectionné qqch mais rien trouvé
             messagebox.showerror("Erreur", "Impossible de trouver les transactions sélectionnées dans les données.")
        # Ne rien faire si aucune transaction n'a été supprimée (cas où found=False pour tous)

    # Appelé quand un filtre est modifié
    def apply_filters(self, *args):
        self.update_transaction_list()

    # Met à jour le contenu du tableau des transactions en fonction des filtres
    def update_transaction_list(self):
        # Vider le tableau actuel
        for item in self.transaction_tree.get_children(): self.transaction_tree.delete(item)

        # Combiner revenus et dépenses pour le filtrage et l'affichage
        all_transactions = [] 
        for item in self.data.get('income', []): all_transactions.append({**item, 'type': 'Revenu', 'category': 'N/A'}) # Ajouter type et catégorie N/A pour revenus
        for item in self.data.get('expenses', []): all_transactions.append({**item, 'type': 'Dépense'}) # Type déjà implicite
        
        selected_month = self.filter_month_var.get()
        selected_category = self.filter_category_var.get()

        # Filtrer les transactions
        filtered_transactions = []
        for item in all_transactions:
            try:
                item_date = datetime.strptime(item['date'], '%Y-%m-%d')
                item_month = item_date.strftime('%Y-%m')
            except (ValueError, KeyError): continue # Ignorer si date invalide

            # Vérifier correspondance mois
            month_match = (selected_month == "Tous" or item_month == selected_month)
            # Vérifier correspondance catégorie
            category_match = (selected_category == "Toutes" or 
                             (item['type'] == 'Dépense' and item.get('category') == selected_category) or 
                             (item['type'] == 'Revenu' and selected_category == "Toutes")) # Les revenus matchent si filtre "Toutes"

            if month_match and category_match: filtered_transactions.append(item)

        # Trier les transactions filtrées par date (plus récentes en premier)
        try: filtered_transactions.sort(key=lambda x: datetime.strptime(x['date'], '%Y-%m-%d'), reverse=True)
        except ValueError:
            print("Erreur lors du tri des transactions par date.")
            messagebox.showerror("Erreur Interne", "Impossible de trier les transactions.")

        # Remplir le tableau avec les transactions filtrées et triées
        fcfa_format = lambda x: f"{x:,.0f} FCFA".replace(',', ' ')
        for i, item in enumerate(filtered_transactions):
            tag = 'evenrow' if i % 2 == 0 else 'oddrow' # Appliquer style alterné
            self.transaction_tree.insert("", "end", values=(
                item['type'], 
                item['date'], 
                item['description'], 
                fcfa_format(item['amount']), 
                item.get('category', 'N/A') # Utiliser N/A si catégorie absente
            ), tags=(tag,))
        
        self.style_treeview() # Réappliquer le style (utile si thème change)

    # Widgets de l'écran Analyse
    def create_analysis_widgets(self):
        content_frame = ctk.CTkFrame(self.analysis_frame, fg_color="transparent")
        content_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        content_frame.grid_columnconfigure(0, weight=1) # Colonne texte
        content_frame.grid_columnconfigure(1, weight=2) # Colonne graphique (plus large)
        content_frame.grid_rowconfigure(1, weight=1) # La ligne du contenu prend l'espace

        ctk.CTkLabel(content_frame, text="Analyse des Dépenses", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 20), sticky="w")

        # Zone pour le résumé textuel
        analysis_text_frame = ctk.CTkFrame(content_frame)
        analysis_text_frame.grid(row=1, column=0, padx=(10, 5), pady=10, sticky="nsew")
        analysis_text_frame.grid_rowconfigure(0, weight=1)
        analysis_text_frame.grid_columnconfigure(0, weight=1)
        self.analysis_results_label = ctk.CTkLabel(analysis_text_frame, text="", font=ctk.CTkFont(size=14), justify="left", anchor="nw", wraplength=350)
        self.analysis_results_label.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")

        # Zone pour le graphique camembert
        self.analysis_chart_frame = ctk.CTkFrame(content_frame)
        self.analysis_chart_frame.grid(row=1, column=1, padx=(5, 10), pady=10, sticky="nsew")
        self.analysis_chart_frame.grid_rowconfigure(0, weight=1)
        self.analysis_chart_frame.grid_columnconfigure(0, weight=1)
        # Label initial qui sera remplacé par le graphique
        self.chart_label = ctk.CTkLabel(self.analysis_chart_frame, text="Chargement du graphique...")
        self.chart_label.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.update_analysis() # Générer l'analyse initiale

    # Met à jour le texte et le graphique de l'analyse des dépenses
    def update_analysis(self):
        expenses = self.data.get('expenses', [])
        if not expenses:
            self.analysis_results_label.configure(text="Aucune dépense enregistrée pour l'analyse.")
            # Nettoyer le graphique précédent s'il existe
            if self.analysis_chart_widget: self.analysis_chart_widget.get_tk_widget().destroy(); self.analysis_chart_widget = None
            self.chart_label.configure(text="Pas de données pour le graphique.", image=None); self.chart_label.grid() # Afficher message
            return

        # Calculer le total dépensé par catégorie
        category_spending = defaultdict(float)
        for expense in expenses:
            category = expense.get('category', 'Non Catégorisé') # Utiliser 'Non Catégorisé' si absent
            category_spending[category] += expense.get('amount', 0)

        if not category_spending:
             self.analysis_results_label.configure(text="Aucune dépense avec catégorie trouvée.")
             if self.analysis_chart_widget: self.analysis_chart_widget.get_tk_widget().destroy(); self.analysis_chart_widget = None
             self.chart_label.configure(text="Pas de données pour le graphique.", image=None); self.chart_label.grid()
             return

        # --- Générer le résumé textuel --- 
        top_category = max(category_spending, key=category_spending.get)
        top_amount = category_spending[top_category]
        fcfa_format = lambda x: f"{x:,.0f} FCFA".replace(',', ' ')
        
        analysis_text = f"Analyse des Dépenses :\n\n"
        analysis_text += f"- Catégorie principale : **{top_category}** ({fcfa_format(top_amount)})\n\n"
        analysis_text += "Détail par Catégorie :\n"
        # Trier les dépenses par montant décroissant
        sorted_spending = sorted(category_spending.items(), key=lambda item: item[1], reverse=True)
        for category, amount in sorted_spending:
            analysis_text += f"  - {category}: {fcfa_format(amount)}\n"
        self.analysis_results_label.configure(text=analysis_text)

        # --- Générer le graphique camembert --- 
        labels = list(category_spending.keys())
        sizes = list(category_spending.values())
        
        # Détruire l'ancien widget graphique s'il existe
        if self.analysis_chart_widget: self.analysis_chart_widget.get_tk_widget().destroy(); self.analysis_chart_widget = None

        try:
            theme = ctk.get_appearance_mode()
            # Définir les couleurs Matplotlib en fonction du thème CTk
            if theme == "Dark":
                bg_color = "#2b2b2b" # Couleur de fond sombre
                text_color = "#ffffff" # Couleur de texte claire
                pie_text_color = "white"
                plt.style.use('dark_background') # Style Matplotlib sombre
            else: # Light or System (assume light for System)
                bg_color = "#ebebeb" # Couleur de fond claire
                text_color = "#000000" # Couleur de texte sombre
                pie_text_color = "black"
                plt.style.use('seaborn-v0_8-pastel') # Style Matplotlib clair

            fig, ax = plt.subplots(figsize=(5, 4), dpi=100)
            fig.patch.set_facecolor(bg_color) # Couleur de fond de la figure
            ax.set_facecolor(bg_color) # Couleur de fond des axes

            # Créer le camembert
            wedges, texts, autotexts = ax.pie(sizes, labels=None, autopct='%1.1f%%', startangle=90, pctdistance=0.85)
            # Ajouter un cercle au centre pour faire un donut chart
            centre_circle = plt.Circle((0,0),0.70,fc=bg_color); fig.gca().add_artist(centre_circle)

            # Configurer la couleur du texte des pourcentages
            for autotext in autotexts: autotext.set_color(pie_text_color); autotext.set_fontsize(9)

            ax.axis('equal') # Assure que le camembert est un cercle
            # Ajouter une légende
            legend = ax.legend(wedges, labels, title="Catégories", loc="center left", bbox_to_anchor=(1.05, 0.5), fontsize=10)
            plt.setp(legend.get_texts(), color=text_color)
            plt.setp(legend.get_title(), color=text_color)
            legend.get_frame().set_facecolor(bg_color)
            legend.get_frame().set_edgecolor(text_color)
            
            plt.title("Répartition des Dépenses", color=text_color)
            plt.tight_layout(rect=[0, 0, 0.85, 1]) # Ajuster layout pour la légende

            # Intégrer le graphique dans Tkinter
            canvas = FigureCanvasTkAgg(fig, master=self.analysis_chart_frame)
            canvas.draw()
            self.analysis_chart_widget = canvas
            canvas.get_tk_widget().grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
            self.chart_label.grid_forget() # Cacher le label initial
            plt.close(fig) # Fermer la figure matplotlib pour libérer la mémoire

        except Exception as e:
            print(f"Erreur lors de la génération du graphique: {e}")
            messagebox.showerror("Erreur Graphique", f"Impossible de générer le graphique: {e}")
            self.chart_label.configure(text="Erreur graphique."); self.chart_label.grid() # Afficher message d'erreur

    # Widgets de l'écran Chat IA
    def create_chat_widgets(self):
        chat_container = ctk.CTkFrame(self.chat_frame)
        chat_container.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        chat_container.grid_columnconfigure(1, weight=1) # Le champ clé API s'étend
        chat_container.grid_rowconfigure(1, weight=1) # L'historique du chat s'étend

        # La clé API OpenRouter est intégrée directement dans le code
        # ATTENTION: Cette pratique n'est pas recommandée pour des applications en production
        # car elle expose la clé API dans le code source.
        self.openrouter_api_key = "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"
        
        # Information sur l'utilisation de l'API
        api_info_label = ctk.CTkLabel(chat_container, text="Chat IA alimenté par DeepSeek via OpenRouter")
        api_info_label.grid(row=0, column=0, columnspan=3, padx=10, pady=(10,0), sticky="w")

        # Zone de texte pour l'historique du chat
        self.chat_history = ctk.CTkTextbox(chat_container, state="disabled", height=300, wrap="word")
        self.chat_history.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

        # Champ pour l'entrée utilisateur
        self.user_input = ctk.CTkEntry(chat_container, placeholder_text="Entrez votre message ici...")
        self.user_input.grid(row=2, column=0, columnspan=2, padx=(10,0), pady=(0,10), sticky="ew")
        self.user_input.bind("<Return>", self.send_chat_message_event) # Lier la touche Entrée
        
        # Bouton Envoyer
        self.send_button = ctk.CTkButton(chat_container, text="Envoyer", command=self.send_chat_message_event)
        self.send_button.grid(row=2, column=2, padx=(5,10), pady=(0,10))

        # Note indiquant que la logique IA n'est pas implémentée (supprimée ou commentée)
        # note_label = ctk.CTkLabel(chat_container, text="Note : La logique de discussion avec l'API doit être implémentée.", font=ctk.CTkFont(size=10), text_color="gray")
        # note_label.grid(row=3, column=0, columnspan=3, padx=10, pady=(0,10), sticky="w")

    # Cette méthode n'est plus nécessaire car la clé API est intégrée directement
    # Elle est conservée comme espace réservé pour d'éventuelles fonctionnalités futures
    def toggle_api_key_visibility(self):
        pass


    # Ajoute un message à la zone d'historique du chat
    def add_to_chat_history(self, sender: str, message: str):
        self.chat_history.configure(state="normal")
        self.chat_history.insert(ctk.END, f"{sender}: {message}\n\n")
        self.chat_history.configure(state="disabled")
        self.chat_history.see(ctk.END)

    # Gère l'événement d'envoi (bouton ou touche Entrée)
    def send_chat_message_event(self, event=None):
        user_message = self.user_input.get().strip()
        if not user_message:
            return
        
        # Effacer le champ d'entrée immédiatement après l'envoi
        self.user_input.delete(0, ctk.END)
        
        # Lancer l'appel API dans un thread séparé
        thread = threading.Thread(target=self.process_chat_message, args=(user_message,))
        thread.start()

    # Traite le message utilisateur et appelle l'API OpenRouter avec DeepSeek
    def process_chat_message(self, user_message):
        # Désactiver les widgets d'entrée pendant le traitement
        self.user_input.configure(state="disabled")
        self.send_button.configure(state="disabled")
        self.add_to_chat_history("Vous", user_message)
        # La ligne d'effacement du champ a été déplacée dans send_chat_message_event

        try:
            # Ajouter le message utilisateur à l'historique pour l'API
            self.chat_history_list.append({"role": "user", "content": user_message})
            
            # Préparer les messages pour l'API (inclure un message système)
            messages_for_api = [
                {"role": "system", "content": "Tu es un assistant utile intégré à une application de suivi de budget. Réponds de manière concise et pertinente aux questions des utilisateurs, potentiellement liées à la gestion de budget ou à des sujets généraux."}
            ] + self.chat_history_list

            # Configuration de la requête pour OpenRouter avec DeepSeek
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.openrouter_api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "budget_tracker_app",  # Identifiant de l'application
                "X-Title": "Budget Tracker"  # Nom de l'application
            }
            
            # Préparation des données pour la requête
            data = {
                "model": "deepseek/deepseek-r1-0528",
                "messages": messages_for_api,
                "max_tokens": 1000  # Limitation nécessaire malgré la clé "unlimited"
            }
            
            # Appel à l'API OpenRouter
            response = requests.post(
                url=url,
                headers=headers,
                data=json.dumps(data)
            )
            
            # Vérification de la réponse
            if response.status_code == 200:
                response_data = response.json()
                ai_message = response_data["choices"][0]["message"]["content"].strip()
                
                # Ajouter la réponse de l'IA à l'historique local et API
                self.add_to_chat_history("Assistant", ai_message)
                self.chat_history_list.append({"role": "assistant", "content": ai_message})
                
                # Limiter la taille de l'historique pour éviter de dépasser les limites de tokens
                MAX_HISTORY_MESSAGES = 10 
                if len(self.chat_history_list) > MAX_HISTORY_MESSAGES:
                    self.chat_history_list = self.chat_history_list[-MAX_HISTORY_MESSAGES:]
            else:
                error_message = f"Erreur API (code {response.status_code}): {response.text}"
                messagebox.showerror("Erreur API", error_message)
                self.add_to_chat_history("Système", f"Erreur: {error_message}")
                # Retirer le dernier message utilisateur de l'historique API car il a échoué
                if self.chat_history_list and self.chat_history_list[-1]["role"] == "user":
                    self.chat_history_list.pop()

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Erreur Connexion API", f"Impossible de se connecter à l'API OpenRouter: {e}")
            self.add_to_chat_history("Système", f"Erreur de connexion API.")
            if self.chat_history_list and self.chat_history_list[-1]["role"] == "user":
                self.chat_history_list.pop()
        except Exception as e:
            messagebox.showerror("Erreur Inconnue", f"Une erreur inattendue est survenue: {e}")
            self.add_to_chat_history("Système", f"Erreur inattendue: {e}")
            print(f"Erreur API inattendue: {e}")
            if self.chat_history_list and self.chat_history_list[-1]["role"] == "user":
                self.chat_history_list.pop()
        finally:
            # Réactiver les widgets d'entrée
            self.user_input.configure(state="normal")
            self.send_button.configure(state="normal")
            # Remettre le focus sur le champ d'entrée
            self.user_input.focus()

    # Fonction utilitaire pour appliquer le mode d'apparence aux couleurs
    # (Nécessaire car CustomTkinter retourne parfois des tuples de couleurs)
    def _apply_appearance_mode(self, color):
        # Retourne la couleur appropriée (index 0 pour Light, index 1 pour Dark)
        if isinstance(color, (list, tuple)):
            # Vérifier si les éléments sont bien des strings (couleurs)
            if len(color) == 2 and isinstance(color[0], str) and isinstance(color[1], str):
                 # S'assurer que les couleurs retournées sont compatibles Matplotlib si nécessaire
                 # Ici, on retourne les couleurs CTk directement, la conversion est faite dans update_analysis
                return color[1] if ctk.get_appearance_mode() == "Dark" else color[0]
            else:
                # Gérer le cas où le tuple/liste ne contient pas les couleurs attendues
                # Retourner une couleur par défaut ou la valeur originale
                print(f"Avertissement: Format de couleur inattendu {color}")
                # Tenter de retourner une couleur par défaut basée sur le thème
                return "#FFFFFF" if ctk.get_appearance_mode() == "Dark" else "#000000"
        elif isinstance(color, str):
            # Si c'est déjà une string, la retourner telle quelle
            return color
        else:
            # Gérer d'autres types inattendus
            print(f"Avertissement: Type de couleur inattendu {type(color)}")
            return "#000000" # Couleur par défaut


