from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
import subprocess
from ai_agents.ai_sdr.sdr.main_orchestrated import main as run_orchestrated_workflow
import os
from openai import OpenAI
app = FastAPI()
load_dotenv()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"]
)

class SearchRequest(BaseModel):
    query: str
    mode: str
class EnhanceRequest(BaseModel):
    query: str

class OrchestratedConfig(BaseModel):
    config: dict

@app.post("/api/v1/orchestrated/run")
async def run_orchestrated(config: OrchestratedConfig):
    try:
        api_key = config.config.get("openai_api_key")
        if not api_key:
            return {"status": "error", "message": "OpenAI API key is required"}
        data_source = config.config.get('data_source', {})
        if data_source and 'type' in data_source and data_source['type'] == 'csv':
            file_path = data_source['file_path']
            if not os.path.exists(file_path):
                return {"status": "error", "message": f"CSV file not found: {file_path}"}
        
        try:
            client = OpenAI(api_key=api_key)
            client.models.list()
        except Exception as e:
            return {"status": "error", "message": f"Invalid OpenAI API key: {str(e)}"}
        
        await run_orchestrated_workflow(config.config)
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
@app.post("/api/v1/enhance")
async def enhance_query(req: EnhanceRequest):
    prompt = req.query.strip()
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {
                    "role": "developer",
                    "content": (
                        """
                       You are a prompt enhancement assistant.

Your task is to take shorthand or vague user prompts and rewrite them into clear, detailed, single-sentence instructions optimized for another LLM agent to convert into a structured DSL (Domain-Specific Language) query.

Your rewritten output must:
- Clearly mention the number of companies asked for in numeric form. If the user does not specify, assume they want 1 companies.
- Include implied company filters such as industry, region, size, business model (B2B/B2C), category tags, and any other metadata if clearly implied
- Avoid ambiguity by expanding abbreviations or fragmentary phrases (e.g., "SaaS" → "software as a service companies")
- Use complete, fluent, factual language in one sentence
- Focus strictly on company-level metadata — do not add contact, employee, or hiring details
- Never ask a question or include example results — only describe the intended search

Do not invent fields that are not implied. Do not return bullet points or multi-line output. Your response should be a single, precise sentence.

                        """
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0,
            max_tokens=100
        )
        print("OpenAI response:", response)
        enhanced = response.choices[0].message.content
        return {"enhanced": enhanced}   
    
    except Exception as e:
        return {"enhanced": prompt, "error": str(e)}
@app.get("/api/v1/search/stream")
async def stream_logs(query: str, mode: str):
    async def event_generator():
        command = f'leadgen dsl --{mode} "{query}"'

        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        for line in iter(process.stdout.readline, ""):
            yield f"data: {line.strip()}\n\n"

        process.stdout.close()
        process.wait()

    return EventSourceResponse(event_generator())