import os
from config.loaded_config import loaded_config
from config.logging import logger
from kafkautils.main import consumer_main
from app.main import main as server_main

# Set default MODE if not specified
if not hasattr(loaded_config, 'MODE'):
    loaded_config.MODE = os.getenv("MODE", "server")

if loaded_config.MODE == "server":
    if __name__ == "__main__":
        server_main()

elif loaded_config.MODE == "consumer":
    import asyncio
    logger.info("Starting Consumer")
    if __name__ == "__main__":
        asyncio.run(consumer_main())

else:
    logger.error(f"MODE '{loaded_config.MODE}' not available")
    logger.error("Available modes: server, consumer")
    logger.error("Set MODE environment variable: MODE=server or MODE=consumer")