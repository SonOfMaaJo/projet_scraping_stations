# Projet de Scraping des Stations de Transport Urbain

Ce projet Python vise à collecter des informations sur les stations de métro, tramway, RER et Transilien de différentes villes françaises à partir de Wikimedia Commons et Wikipédia. Les données collectées sont ensuite sauvegardées au format JSON et CSV.

## Structure du Projet

```
projet_scraping_capstone_v2/
├── do/
│   ├── scraper.py             # Script pour scraper une URL de catégorie spécifique
│   ├── scraper_module.py      # Module principal de scraping (anciennement scraper_module_v4.py)
│   └── run_all_scrapes.py     # Script pour scraper toutes les URLs listées dans input/urls.txt
├── input/
│   └── urls.txt               # Fichier contenant la liste des URLs de catégories à scraper
└── output/
    ├── (fichiers de sortie existants)
    └── (fichiers de sortie générés par les scripts)
```

## Installation

1.  **Cloner le dépôt** (si vous êtes sur GitHub) ou assurez-vous d'avoir tous les fichiers du projet.
2.  **Créer un environnement virtuel** (recommandé) :
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
3.  **Installer les dépendances Python** :
    ```bash
    pip install requests beautifulsoup4 tqdm
    ```
    *(Note: Un fichier `requirements.txt` sera ajouté ultérieurement pour simplifier cette étape.)*

## Utilisation

### 1. Scraper une seule catégorie de stations

Utilisez le script `scraper.py` pour scraper une URL de catégorie spécifique.

```bash
python do/scraper.py <url_de_la_categorie> [nom_fichier_sortie]
```

*   `<url_de_la_categorie>`: L'URL de la page de catégorie Wikimedia Commons/Wikipédia à scraper (obligatoire).
*   `[nom_fichier_sortie]`: (Optionnel) Le nom de base pour les fichiers de sortie JSON et CSV. Si non spécifié, les fichiers seront nommés `stations_scraped.json` et `stations_scraped.csv`.

**Exemples :**

```bash
# Scraper les stations du tramway de Bordeaux avec le nom par défaut
python do/scraper.py "https://commons.wikimedia.org/wiki/Category:Stations_of_Bordeaux_Tramway_by_name"

# Scraper les stations du métro de Paris et sauvegarder sous "paris_metro"
python do/scraper.py "https://commons.wikimedia.org/wiki/Category:Stations_of_the_Paris_Metro_by_name" "paris_metro"
```

Les fichiers de sortie seront générés dans le dossier `output/`.

### 2. Scraper toutes les catégories de stations

Utilisez le script `run_all_scrapes.py` pour scraper toutes les URLs listées dans `input/urls.txt`.

```bash
python do/run_all_scrapes.py
```

Ce script lira chaque URL du fichier `input/urls.txt`, effectuera le scraping, et agrègera toutes les données dans un seul fichier `stations_complete.json` et `stations_complete.csv` dans le dossier `output/`.

## Fichiers d'entrée

Le fichier `input/urls.txt` contient une liste d'URLs, une par ligne, représentant les catégories de stations à scraper. Vous pouvez modifier ce fichier pour inclure ou exclure des URLs selon vos besoins.

## Sorties

Les données collectées sont sauvegardées dans le dossier `output/` au format JSON et CSV.

---
