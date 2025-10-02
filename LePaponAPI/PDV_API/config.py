import os

# Base URL central da API (pode ser sobrescrita via variável de ambiente API_BASE_URL)
BASE_URL = os.getenv("API_BASE_URL", "http://lepapon.api:3000").rstrip('/')
