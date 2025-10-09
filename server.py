import os
from config.loaded_config import loaded_config

# Set default MODE if not specified
if not hasattr(loaded_config, 'MODE'):
    loaded_config.MODE = os.getenv("MODE", "server")

if loaded_config.MODE == "server":
    from app.main import main as server_main

    if __name__ == "__main__":
        server_main()

elif loaded_config.MODE == "consumer":
    import asyncio
    from ai_agents.leadgen.api.main import consumer_main

    print("Starting Consumer")
    if __name__ == "__main__":
        asyncio.run(consumer_main())

else:
    print(f"MODE '{loaded_config.MODE}' not available")
    print("Available modes: server, consumer")
    print("Set MODE environment variable: MODE=server or MODE=consumer")