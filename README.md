# Suivi Budget Étudiant

<!-- Logo du projet -->
<p align="center">
  <img src="https://i.imgur.com/VEhhjAo.png" alt="Quiz Application Logo" width="300" />
</p>

<!-- Ligne de séparation animée -->
<img src="https://github.com/AnderMendoza/AnderMendoza/raw/main/assets/line-neon.gif" width="100%" />

<!-- Effet typing animé -->
[![Typing SVG](https://readme-typing-svg.demolab.com/?lines=Bienvenue+ici+les+menbres+du+groupe+11;+ici+C'est+le+depot+des+projets;De+Mr+Nabolé+Partagez+vos+codes+Python+et+C&speed=90&size=30&color=F20C39&background=FF20A500&width=800&height=80)](https://git.io/typing-svg)





## `Je vous demande de faire part dans le groupe Whatsapp apres avoir tester le projet  `

                                 
## `CLONE REPO & INSTALLATION DEPENDENCIES suivez les commandes un a un Merci `

```bash
https://github.com/DARKMAN226/PYTHON-PROJECT.git
```

```bash
cd PYTHON-PROJECT
```


## Description

Cette application de bureau simple permet aux étudiants (ou à toute autre personne) de suivre leurs revenus et leurs dépenses. Elle offre une interface graphique pour ajouter des transactions, visualiser un solde, analyser les dépenses par catégorie, filtrer les transactions et interagir avec une IA.

Fonctionnalités principales :
*   Ajout de revenus et de dépenses avec description, montant, date et catégorie (pour les dépenses).
*   Tableau de bord affichant le solde actuel, le total des revenus et le total des dépenses.
*   Liste détaillée des transactions avec possibilité de filtrer par mois et par catégorie.
*   **Suppression des transactions sélectionnées** dans la liste.
*   Analyse visuelle des dépenses par catégorie via un graphique camembert.
*   Choix du thème d'apparence (Clair/Sombre).
*   Sauvegarde automatique des données dans un fichier `budget_data.json`.
*   **Section "Chat IA" fonctionnelle** utilisant l'API OpenAI pour répondre aux questions (nécessite une clé API valide).

## Prérequis

*   Python 3.x
*   Les bibliothèques listées ci-dessous.

## Installation des dépendances

Installez les dépendances nécessaires via pip :

```bash
pip install customtkinter matplotlib Pillow openai
```

(Si un fichier `requirements.txt` est fourni, vous pouvez aussi utiliser `pip install -r requirements.txt`)

## Lancement de l'application

Pour démarrer l'application, exécutez le fichier `main.py` depuis le répertoire du projet :

```bash
python main.py
```

## Utilisation du Chat IA

1.  Rendez-vous dans la section "Chat IA".
2.  Assurez-vous que votre clé API OpenAI est correctement entrée dans le champ prévu (actuellement pré-remplie dans le code pour test, **il est fortement recommandé de ne pas stocker de clés API directement dans le code pour des applications réelles**).
3.  Posez votre question dans le champ de saisie et appuyez sur Entrée ou cliquez sur "Envoyer".
4.  L'assistant répondra dans la zone d'historique.

**Note sur la clé API OpenAI :** L'application nécessite une clé API OpenAI valide pour que la fonctionnalité de chat fonctionne. La clé est actuellement codée en dur dans `app.py`. Pour une utilisation sécurisée, il est préférable de gérer la clé via des variables d'environnement ou un fichier de configuration non versionné.

## Fichiers du projet

*   `main.py`: Point d'entrée de l'application.
*   `app.py`: Contient la logique principale et l'interface graphique de l'application (classe `BudgetApp`).
*   `budget_data.json`: Fichier où les données des transactions sont sauvegardées (créé au premier lancement si inexistant).
*   `README.md`: Ce fichier.

