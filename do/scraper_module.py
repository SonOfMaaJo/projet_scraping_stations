import requests
from bs4 import BeautifulSoup
from urllib.parse import unquote_plus, urlparse, urljoin
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import json
import csv
import logging

# Configuration du logging pour ce module
logger = logging.getLogger(__name__)
# S'assurer que le logger a des handlers si ce module est exécuté seul
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class BaseScraper:
    """
    Classe de base pour les scrapers, fournissant des fonctionnalités communes
    comme le téléchargement et le parsing de contenu HTML avec gestion des erreurs.
    """
    def __init__(self, base_url: str):
        """
        Initialise le BaseScraper avec une URL de base.

        Args:
            base_url (str): L'URL de base pour les requêtes.
        """
        self.base_url = base_url

    def parse(self, url: str = None, max_retries: int = 3, backoff_factor: float = 0.5):
        """Downloads the HTML content of a page and parse to BeautifulSoup object with retries."""
        target_url = url or self.base_url
        for attempt in range(max_retries):
            try:
                # Ajout d'un timeout pour éviter les blocages infinis
                response = requests.get(target_url, timeout=10)
                # Lève une exception pour les codes d'erreur HTTP (4xx ou 5xx)
                response.raise_for_status()
                return BeautifulSoup(response.text, 'html.parser')
            except requests.exceptions.RequestException as e:
                logger.warning(f"Erreur réseau lors du scraping de {unquote_plus(target_url)} (tentative {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    sleep_time = backoff_factor * (2 ** attempt)
                    logger.info(f"Réessai dans {sleep_time:.1f} secondes...")
                    time.sleep(sleep_time)
                else:
                    raise Exception(f"Échec après {max_retries} tentatives pour charger {unquote_plus(target_url)}: {e}")
            except Exception as e:
                raise Exception(f"Erreur inattendue lors du parsing de {unquote_plus(target_url)}: {e}")
        return None # Ne devrait pas être atteint


class Scraper(BaseScraper):
    """
    Scraper spécifique pour collecter des informations sur les stations à partir
    de pages de catégories Wikimedia Commons/Wikipédia.
    """
    def __init__(self, url: str = "https://commons.wikimedia.org/wiki/Accueil", max_workers: int = 5):
        """
        Initialise le Scraper.

        Args:
            url (str, optional): L'URL de la page de catégorie de départ.
                                 Par défaut à l'accueil de Wikimedia Commons.
            max_workers (int): Nombre maximal de threads pour le scraping parallèle des pages de stations.
        """
        super().__init__(url)
        self.parsedUrl = urlparse(url)
        self.stations = dict()  # Dictionnaire pour stocker les données des stations
        self.visited = set()    # Ensemble pour garder une trace des URLs déjà visitées
        self.max_workers = max_workers

    def extract_next_page(self, soup: BeautifulSoup) -> str | None:
        """
        Extrait le lien vers la page suivante dans une catégorie Wikimedia Commons/Wikipédia.

        Args:
            soup (BeautifulSoup): L'objet BeautifulSoup de la page actuelle.

        Returns:
            str | None: L'URL de la page suivante, ou None si non trouvée.
        """
        next_page = None
        # Recherche du lien "next page" basé sur le titre de la catégorie
        for a in soup.find_all('a', title=self.parsedUrl.path[6:].replace('_', ' ')):
            if 'next page' in a.get_text().lower():
                next_page = urljoin(f"{self.parsedUrl.scheme}://{self.parsedUrl.netloc}", a.get('href'))
                break
        return next_page

    def runquote(self, el: str) -> str | None:
        """
        Décode une chaîne URL-encodée et remplace les retours à la ligne par des espaces.

        Args:
            el (str): La chaîne à décoder.

        Returns:
            str | None: La chaîne décodée et nettoyée, ou None si l'entrée est None.
        """
        return unquote_plus(el.replace('\n', ' ')) if el else None

    def scrape_station(self, station_link: str) -> tuple[str | None, dict]:
        """
        Scrape une seule page de station pour en extraire le nom et les données.

        Args:
            station_link (str): Le lien relatif ou absolu vers la page de la station.

        Returns:
            tuple[str | None, dict]: Un tuple contenant le nom de la station (ou None)
                                     et un dictionnaire de ses données.
        """
        full_url = urljoin(f"{self.parsedUrl.scheme}://{self.parsedUrl.netloc}", station_link)
        station_name = None
        station_data = {}

        try:
            soup1 = self.parse(full_url)
            # Extrait le nom de la station à partir du titre H1
            station_name = soup1.find('h1').get_text(strip=True).replace('Category:', '')

            # Logique pour extraire la localisation (spécifique à certains sites)
            class_l = ["mw-kartographer-maplink", " mw-kartographer-link"] if self.parsedUrl.netloc == "fr.wikipedia.org" else "plainlinksneverexpand"
            localisation = soup1.tbody.find('span', class_=class_l) if soup1.tbody else None
            if localisation:
                local = self.runquote(localisation.get_text())
                station_data['Localisation'] = local

            # Logique pour extraire les données du tableau (spécifique à certains sites)
            class_cell = "wdinfo_nomobile" if self.parsedUrl.netloc == "commons.wikimedia.org" else None
            scope = 'row' if self.parsedUrl.netloc == "fr.wikipedia.org" else None
            if soup1.tbody:
                # Parcourt les lignes du tableau pour extraire les paires clé-valeur
                for tr in soup1.tbody.find_all('tr', class_=class_cell)[1:]:
                    if tr.find('th', scope=scope):
                        station_data[self.runquote(tr.th.get_text())] = self.runquote(tr.td.get_text())

        except Exception as e:
            logger.error(f"Error scraping {station_link}: {e}")

        return station_name, station_data
    
    def extract_station_links(self, soup: BeautifulSoup) -> list[str]:
        """
        Extrait tous les liens vers les pages de stations à partir d'une page de catégorie.

        Args:
            soup (BeautifulSoup): L'objet BeautifulSoup de la page de catégorie.

        Returns:
            list[str]: Une liste d'URLs de stations.
        """
        station_links = []
        # Les liens de stations sont généralement dans des div avec la classe "mw-category-group"
        for div in soup.find_all('div', class_="mw-category-group"):
            for a in div.find_all('a', href=True):
                station_links.append(a.get('href'))
                
        return station_links


    def recursive_scrape(self, url: str = None):
        """
        Scrape récursivement les informations des stations à partir d'une URL de catégorie
        en gérant la pagination et en utilisant la parallélisation.

        Args:
            url (str, optional): L'URL de la catégorie de départ. Si None, utilise self.base_url.
        """
        target_url = url or self.base_url
        if target_url in self.visited:
            return
        self.visited.add(target_url)

        try:
            soup = self.parse(target_url)
        except Exception as e:
            logger.error(f"Error parsing initial URL {target_url}: {e}")
            return

        logger.info(f"Fetching: {unquote_plus(target_url)}")
        time.sleep(0.5) # Délai pour éviter de surcharger le serveur

        station_links = self.extract_station_links(soup)
        next_page_url = self.extract_next_page(soup)
        # Boucle pour gérer la pagination et collecter tous les liens de stations
        while next_page_url:
            try:
                soup = self.parse(next_page_url)
                station_links.extend(self.extract_station_links(soup))
                next_page_url = self.extract_next_page(soup)
            except Exception as e:
                logger.error(f"Error parsing next page {next_page_url}: {e}")
                return
                
        logger.info(f"Scraping {len(station_links)} stations...")

        # Scraping parallèle des pages de stations avec barre de progression
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(self.scrape_station, link) for link in station_links]

            for future in tqdm(as_completed(futures), total=len(futures), desc="Scraping stations"):
                name, data = future.result()
                if name:
                    self.stations[name] = data

        logger.info('Batch done!')
    
    @classmethod
    def save_as_json(cls, stations: dict = None, filename: str = "stations.json"):
        """
        Sauvegarde les données des stations dans un fichier JSON.

        Args:
            stations (dict, optional): Dictionnaire des données des stations. Si None, ne fait rien.
            filename (str): Nom du fichier JSON de sortie.
        """
        if not stations:
            logger.warning("No data to save to JSON.")
            return

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(stations, f, ensure_ascii=False, indent=4)
        logger.info(f"Data saved to {filename}")
        
    @classmethod
    def save_as_csv(cls, stations: dict = None, filename: str = "stations.csv"):
        """
        Sauvegarde les données des stations dans un fichier CSV.

        Args:
            stations (dict, optional): Dictionnaire des données des stations. Si None, ne fait rien.
            filename (str): Nom du fichier CSV de sortie.
        """
        if not stations:
            logger.warning("No data to save to CSV.")
            return

        # Récupère toutes les clés possibles pour les en-têtes de colonne
        all_keys = set()
        for station_data in stations.values():
            all_keys.update(station_data.keys())

        # Trie les clés pour un ordre cohérent
        all_keys = sorted(all_keys)

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Écrit l'en-tête
            writer.writerow(["Station Name"] + all_keys)
            # Écrit les lignes de données
            for station_name, station_data in stations.items():
                row = [station_name] + [station_data.get(k, '') for k in all_keys]
                writer.writerow(row)

        logger.info(f"Data saved to {filename}")