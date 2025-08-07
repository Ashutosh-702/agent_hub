import uvicorn
from config.loaded_config import loaded_config

if __name__ == "__main__":
    uvicorn.run("ai_agents.leadgen.api.main:app", host="0.0.0.0", port=80,workers=1,reload=loaded_config.debug)
