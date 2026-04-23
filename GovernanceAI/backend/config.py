from dotenv import load_dotenv
import os

load_dotenv()

APP_NAME = os.getenv("APP_NAME","GovernanceGPT")
APP_VERSION = os.getenv("APP_VERSION","0.1.0")

# CLAUDE API
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

#Database
_base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_PATH = os.getenv("DATABASE_PATH", os.path.join(_base_dir, "governance.db"))

#MLFlow
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "./mlflow")

