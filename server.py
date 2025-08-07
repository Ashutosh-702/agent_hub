import uvicorn
from config.loaded_config import loaded_config

if __name__ == "__main__":
    # Use False for production stability instead of loaded_config.debug
    uvicorn.run("ai_agents.leadgen.api.main:app", host="0.0.0.0", port=80, workers=1, reload=False)
