# main.py
from config.settings import settings
from src.app import create_app
from src.utils.logger import logger
from src.schemas.payloads import Position, ClosePosition, ModifyPosition
from src.services.mt5_client import MT5Client as Metatrader
from utils.tools import getEnvValue

# Flask Application instance
app = create_app()

if __name__ == "__main__":
    logger.info(f"Starting server on {settings.host}:{settings.port}")
    app.run(host=settings.host, port=settings.port)
