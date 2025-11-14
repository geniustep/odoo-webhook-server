import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file (if available)
load_dotenv()

# Odoo API configuration
ODOO_URL = os.getenv("ODOO_URL", "https://app.propanel.ma")

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("odoo_webhook")