import sys
import os
import argparse
import logging
from scraper_module import Scraper

# Configuration du logging pour ce script
# Les messages seront affichés sur la console avec un format standard.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    Fonction principale du script scraper.py.
    Elle analyse les arguments en ligne de commande, initialise le scraper,
    effectue le scraping et sauvegarde les données.
    """
    # Configuration de l'analyseur d'arguments en ligne de commande
    parser = argparse.ArgumentParser(description="Scrape des informations de stations à partir d'une URL de catégorie.")
    parser.add_argument("url_stations", type=str,
                        help="L'URL de la page de catégorie Wikimedia Commons/Wikipédia à scraper.")
    parser.add_argument("--output_name", type=str, default="stations_scraped",
                        help="Nom de base pour les fichiers de sortie JSON et CSV (par défaut: stations_scraped).")

    args = parser.parse_args() # Analyse les arguments fournis par l'utilisateur

    url_stations = args.url_stations
    output_filename_base = args.output_name

    # Détermine les chemins absolus pour le dossier de sortie
    doc_script = os.path.dirname(os.path.abspath(__file__))
    doc_project = os.path.dirname(doc_script)
    doc_output = os.path.join(doc_project, "output")
    
    # Crée le dossier de sortie s'il n'existe pas
    os.makedirs(doc_output, exist_ok=True)

    logger.info(f"Démarrage du scraping pour l'URL : {url_stations}")
    
    # Initialise l'objet Scraper avec l'URL fournie
    scraper = Scraper(url=url_stations)
    
    # Lance le processus de scraping récursif
    scraper.recursive_scrape()

    # Construit les chemins complets pour les fichiers de sortie JSON et CSV
    file_json = os.path.join(doc_output, f"{output_filename_base}.json")
    file_csv = os.path.join(doc_output, f"{output_filename_base}.csv")
    
    # Sauvegarde les données collectées
    Scraper.save_as_json(scraper.stations, file_json)
    Scraper.save_as_csv(scraper.stations, file_csv)
    
    logger.info(f"Scraping terminé. Données sauvegardées sous {output_filename_base}.json et {output_filename_base}.csv")

if __name__ == "__main__":
    main()
