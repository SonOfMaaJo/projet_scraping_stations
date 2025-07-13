import os
import logging
from scraper_module import Scraper

# Configuration du logging pour ce script
# Les messages seront affichés sur la console avec un format standard.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_all_scrapes():
    """
    Fonction principale pour orchestrer le scraping de toutes les URLs.
    Elle lit les URLs depuis input/urls.txt, lance le scraper pour chaque URL,
    agrège les résultats et les sauvegarde.
    """
    # Détermine les chemins absolus pour les dossiers input et output
    doc_script = os.path.dirname(os.path.abspath(__file__))
    doc_project = os.path.dirname(doc_script)
    doc_input = os.path.join(doc_project, "input")
    doc_output = os.path.join(doc_project, "output")
    
    # Crée le dossier de sortie s'il n'existe pas
    os.makedirs(doc_output, exist_ok=True)

    urls_file = os.path.join(doc_input, "urls.txt")
    all_urls = []
    
    # Tente de lire les URLs depuis le fichier input/urls.txt
    try:
        with open(urls_file, 'r') as f:
            all_urls = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        logger.error(f"Erreur: Le fichier {urls_file} n'a pas été trouvé. Assurez-vous qu'il existe et contient les URLs.")
        return

    all_stations_data = {} # Dictionnaire pour agréger toutes les données de stations

    # Boucle sur chaque URL pour lancer le scraping
    for url in all_urls:
        logger.info(f"Démarrage du scraping pour : {url}")
        scraper = Scraper(url=url) # Initialise un nouveau scraper pour chaque URL
        scraper.recursive_scrape() # Lance le scraping récursif
        
        # Ajoute les stations collectées à l'ensemble des données
        all_stations_data.update(scraper.stations)
        logger.info(f"Scraping terminé pour : {url}. Total de stations collectées jusqu'à présent : {len(all_stations_data)}")

    # Construit les chemins complets pour les fichiers de sortie finaux
    final_json_file = os.path.join(doc_output, "stations_complete.json")
    final_csv_file = os.path.join(doc_output, "stations_complete.csv")

    # Sauvegarde toutes les données agrégées
    Scraper.save_as_json(all_stations_data, final_json_file)
    Scraper.save_as_csv(all_stations_data, final_csv_file)
    logger.info("Scraping complet terminé. Données sauvegardées dans stations_complete.json et stations_complete.csv")

if __name__ == "__main__":
    run_all_scrapes()
