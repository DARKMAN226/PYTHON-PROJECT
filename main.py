# Fichier principal pour lancer l'application les ✌️

# Cette ligne sert importer la classe BudgetApp depuis le fichier app.py
from app import BudgetApp
# On importe aussi customtkinter pour pouvoir définir le thème avant de lancer l'app (Claire ou sombre)
import customtkinter as ctk

ctk.set_appearance_mode("dark")  

ctk.set_default_color_theme("blue")  

if __name__ == "__main__":
    
    app = BudgetApp()

    app.mainloop()

