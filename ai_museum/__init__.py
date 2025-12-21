from dotenv import load_dotenv
from loguru import logger


if not load_dotenv():
    logger.warning("No variables with loaded from dotenv")
