from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
import subprocess
from ai_agents.ai_sdr.sdr.main_orchestrated import main as run_orchestrated_workflow
import json
import os
from openai import OpenAI
from ai_agents.leadgen.prompt_enhancer import analyze_prompt, enhance_prompt
from ai_agents.leadgen.workflow.prompt_reader import submit_company_data

load_dotenv()
app = FastAPI()

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
class FormSubmission(BaseModel):
    prompt: str          
    industry: str        
    is_b2b: str          
    employee_count: str  
    hq: str 


@app.post("/api/v1/orchestrated/run")
async def run_orchestrated(config: OrchestratedConfig):
    try:
        query=config.config.get("query", "")
        print(f"🔍 Running orchestrated workflow with Prompt: {query}")
        if query:
            try:
                print("🧾 Running DSL query api...")
                result = subprocess.run(
                    ["leadgen", "dsl", "--company", query],
                    check=True,
                    capture_output=True,
                    text=True
                )
                print("✅ DSL query completed.")
                print("🧾 DSL STDOUT:")
                print(result.stdout)
            except subprocess.CalledProcessError as e:
                print("❌ DSL query failed:", e.stderr)
                return {"status": "error", "message": "DSL query failed."}
        search_query = config.config.get("search_query")
        target_executives = config.config.get("target_executives")
        # target_executives = input("List the job titles or executive roles you want to target (e.g., CEO, CTO, VP of Sales): ").strip()
        config.config.setdefault("custom_prompts", {})

        if search_query:
            web_enrichment_prompt = f"""Relevance Criteria (for judgment only):

Evaluate whether the following company matches this criteria:

{search_query}

Begin your research now using the web search tool to determine if companies match these criteria."""
            config.config["custom_prompts"]["web_enricher_user_prompt"] = web_enrichment_prompt

        if target_executives:
            config.config["custom_prompts"]["prospect_enricher_target_executives"] = target_executives

        print("🧪 Final config being passed to orchestrator:")
        print(json.dumps(config.config, indent=2))
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

@app.post("/api/v1/prompt/enhance")
async def enhance_prompt_endpoint(request: dict):
    try:
        prompt = request.get("prompt", "")
        answers = request.get("answers")
        
        if answers is None:
            result = analyze_prompt(prompt)
            return {
                "questions": result.get('questions', []),
                "enhanced_initial_input": result.get('enhanced_initial_input', {}),
                "relevance_criteria_template": result.get('relevance_criteria_template', {}),
                "extracted_criteria": result.get('enhanced_initial_input', {}).get('extracted_criteria', {})
            }
        else:
            result = enhance_prompt(prompt, answers)
            return {
                "enhanced_prompt": result.get('enhanced_prompt', prompt)
            }
            
    except Exception as e:
        return {"error": str(e)}

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



@app.post("/api/v1/sheets/upload_data_from_form")
async def upload_data_from_form(data: FormSubmission):
    try:
        sheet_data = {
            "prompt": data.prompt,
            "industry": data.industry,
            "is_b2b": data.is_b2b,
            "employee_count": data.employee_count,
            "hq": data.hq,
        }
        response = submit_company_data(sheet_data)
        if response.get("status") == "error":
            print(f"Error while submitting data to Google Sheets: {response.get('message', 'Failed to submit data to Google Sheets.')}")
            return {"status": "error", "message": response.get("message", "Failed to submit data to Google Sheets.")}
        print(f"📤 Data submitted to Google Sheets: {response}")
        return response
    except Exception as e:
        return {"status": "error", "message": str(e)}