from sqlalchemy import URL
from dotenv import load_dotenv
from pathlib import Path
import os

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent



# =============================================================================
# APP DB CONF
# =============================================================================


DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

# APP_CONN_STRING = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

APP_CONN_STRING = URL.create(
    drivername="postgresql+psycopg2",
    username=DB_USER,
    password=DB_PASS,
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME
)


# =============================================================================
# API KEY CONF
# =============================================================================

# TODO: Por ahora las api key estarn quemadas en settings.py, la idea es que estas se puedan configurar y se queden guardadas en la db
# TODO: los campos de la db que en el futuro contengan las apikey deben estar encriptadas.


GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DEEP_SEEK_API_KEY = os.getenv("DEEP_SEEK_API_KEY")




# =============================================================================
# GRAFANA CONF
# =============================================================================

GRAFANA_URL = os.getenv("GRAFANA_URL")
GRAFANA_ADMIN_USER = os.getenv("GRAFANA_ADMIN_USER")
GRAFANA_ADMIN_PASSWORD = os.getenv("GRAFANA_ADMIN_PASSWORD")
GRAFANA_SERVICE_ACCOUNT_TOKEN = os.getenv("GRAFANA_SERVICE_ACCOUNT_TOKEN")
GRAFANA_SERVICE_ACCOUNT_ID = os.getenv("GRAFANA_SERVICE_ACCOUNT_ID")






if __name__=="__main__":
    print(ROOT)



