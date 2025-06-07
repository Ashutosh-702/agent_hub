# Azure DevOps Agent Hub Integration Instructions

## Overview
These instructions will help you integrate the ai_sdr codebase into the Azure DevOps agent_hub repository.

## Steps to Complete the Integration

### 1. Clone the Agent Hub Repository
Navigate to the parent directory and clone the repository:

```bash
cd /Users/ahmedropewala/PycharmProjects/etc1
git clone git@ssh.dev.azure.com:v3/GoFynd/SupplyChainGroup/agent_hub
cd agent_hub
```

### 2. Create Directory Structure
Create a dedicated directory for the AI SDR agent within the agent_hub:

```bash
mkdir -p agents/ai_sdr
```

### 3. Copy AI SDR Codebase
Copy the entire ai_sdr codebase to the new location:

```bash
cp -r ../ai_sdr/* agents/ai_sdr/
```

### 4. Update Import Paths (if needed)
After moving, you may need to update any absolute import paths in the code. The current codebase uses relative imports which should work fine.

### 5. Update CLAUDE.md
Update the project instructions to reflect the new directory structure:

```bash
cd agents/ai_sdr
# Edit CLAUDE.md to update paths and add agent_hub context
```

### 6. Test the Integration
Verify that the moved codebase still works:

```bash
cd agents/ai_sdr
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python sdr/main.py
```

### 7. Commit to Git
Once everything is working:

```bash
cd /Users/ahmedropewala/PycharmProjects/etc1/agent_hub
git add agents/ai_sdr
git commit -m "Add AI SDR agent to agent hub

- Integrated complete AI SDR workflow system
- Includes LangGraph orchestration and OpenAI integration
- Supports HubSpot CRM integration
- Added comprehensive logging system with clean/detailed modes

🤖 Generated with Claude Code"
git push origin main
```

## Directory Structure After Integration

```
agent_hub/
├── agents/
│   └── ai_sdr/
│       ├── CLAUDE.md
│       ├── requirements.txt
│       ├── sdr/
│       │   ├── __init__.py
│       │   ├── graph.py
│       │   ├── logging_config.py
│       │   ├── main.py
│       │   ├── models.py
│       │   ├── nodes/
│       │   ├── prompts.py
│       │   └── validate_models.py
│       └── venv/
└── (other agent_hub contents)
```

## Notes
- The AI SDR agent is now a standalone module within the agent hub
- All existing functionality should be preserved
- The logging improvements implemented earlier are included
- Environment variables (.env) will need to be recreated in the new location