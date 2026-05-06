from dotenv import load_dotenv
import os
load_dotenv()

APP_NAME = os.getenv("APP_NAME","DataDialogue")
APP_VERSION = os.getenv("APP_VERSION", "0.1.0")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
_base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE_DB_PATH  = os.getenv("SAMPLE_DB_PATH", "sample.db")
APP_DB_PATH     = os.getenv("APP_DB_PATH", "datadialogue.db")


#MLFlow
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI","./mlflow")