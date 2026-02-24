import os

from dotenv import load_dotenv

from logger import logger

load_dotenv()

TOKEN = os.getenv("TOKEN")

ADMIN_USER_ID = 556864778576986144
ADMIN_ROLES = [1231334945041944628, 1231330785886212177, 1240356360604881027]
TICKETS_CATEGORY_ID = 1348431299290857552

PROTECTED_ROLES = [
    1245792247916793877,
    1240356360604881027,
    1231334945041944628,
    1378339428593963161,
]

IGNORED_CATEGORIES = [
    1348431299290857552,
]

API_BASE_URL = "https://atlas.collapseloader.org"
CLIENTS = []
FABRIC_CLIENTS = []
FORGE_CLIENTS = []

def _fetch_clients_from_api(endpoint: str) -> list:
    """Helper function to fetch clients from API."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/{endpoint}",
            headers={"User-Agent": "CollapseBot"},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        if isinstance(data, dict) and "data" in data:
            return data["data"]
        elif isinstance(data, list):
            return data
        else:
            logger.warning(f"Unexpected API response format from {endpoint}: {type(data)}")
            return []
    except requests.RequestException as e:
        logger.error(f"Failed to fetch clients from {endpoint}: {e}")
        return []

try:
    import requests
    
    all_clients = _fetch_clients_from_api("clients")
    CLIENTS = [client["name"] for client in all_clients if client.get("show", True)]
    logger.info(f"Loaded {len(CLIENTS)} clients from API")
    
    fabric_clients = _fetch_clients_from_api("fabric-clients")
    FABRIC_CLIENTS = [client["name"] for client in fabric_clients if client.get("show", True)]
    logger.info(f"Loaded {len(FABRIC_CLIENTS)} Fabric clients from API")
    
    forge_clients = _fetch_clients_from_api("forge-clients")
    FORGE_CLIENTS = [client["name"] for client in forge_clients if client.get("show", True)]
    logger.info(f"Loaded {len(FORGE_CLIENTS)} Forge clients from API")
    
except Exception as e:
    logger.error(f"Failed to fetch clients from API: {e}")
    CLIENTS = []
    FABRIC_CLIENTS = []
    FORGE_CLIENTS = []
