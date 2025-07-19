import os

from dotenv import load_dotenv

load_dotenv()

# Bot configuration
TOKEN = os.getenv("TOKEN")

# Discord IDs
ADMIN_USER_ID = 556864778576986144
ADMIN_ROLES = [1231334945041944628, 1231330785886212177, 1240356360604881027]
TICKETS_CATEGORY_ID = 1348431299290857552

# Protected mention roles
PROTECTED_ROLES = [
    1245792247916793877,  # Co-Owner
    1240356360604881027,  # Admin
    1231334945041944628,  # Owner
    1378339428593963161,  # Support
]

# Ignored categories for automatic response
IGNORED_CATEGORIES = [
    1348431299290857552,
]

# API endpoints
API_BASE_URL = "https://web.collapseloader.org/api"
