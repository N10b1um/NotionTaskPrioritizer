import json
from datetime import datetime
import google.genai as genai
import config

ai_client = genai.Client(api_key=config.AI_TOKEN)

def evaluate_tasks(pending: list, done: list, context: str) -> dict:
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    day_of_week = now.strftime("%A")
    current_hour = now.hour
    
    pending_str = ""
    for t in pending:
        dead_str = f", Deadline: {t['deadline']}" if t['deadline'] else ""
        pending_str += f"- ID: {t['id']}\n  Name: {t['name']}\n  Efforts: {t['efforts']}{dead_str}\n  Desc: {t['desc']}\n\n"

    done_str = "\n".join([f"- {t['name']}" for t in done[:15]])

    full_system_instruction = f"""
    {context}
    
    CRITICAL LOGIC:
    - Priority Formula: (Priority = Importance * 8 + Urgency * 4 - Efforts).
    - Tiers: Tier 1 (USA/Math/Eng) > Tier 2 (FTC/ML/Startup) > Tier 3 (School noise).
    
    RESPONSE STRUCTURE:
    You MUST return a JSON OBJECT with two keys: 
    1. "evaluations": an object where keys are Notion Task IDs.
    2. "new_tasks": an array of objects.
    
    MENTORSHIP STYLE:
    Your 'reason' must be a tactical advice (1-2 sentences) in Russian.
    - Mention the 2.5h commute for light tasks.
    - Suggest skipping/faking Tier 3.
    - If current_hour > 21, prioritize sleep.
    """

    user_query = f"""
    DATE: {today} ({day_of_week}), TIME: {current_hour}:00
    RECENTLY DONE: {done_str if done_str else "None"}
    PENDING TASKS:
    {pending_str}
    
    TASK: Re-evaluate everything. Return strictly the JSON object.
    """

    response = ai_client.models.generate_content(
        model="gemini-3-flash-preview", 
        contents=user_query,
        config={
            "response_mime_type": "application/json",
            "system_instruction": full_system_instruction
        },
    )
    
    try:
        raw_text = response.text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text.replace("```json", "").replace("```", "").strip()
            
        data = json.loads(raw_text)
        
        if isinstance(data, list):
            formatted_evals = {}
            for item in data:
                task_id = item.get("id") or item.get("ID")
                if task_id:
                    formatted_evals[task_id] = {
                        "importance": item.get("importance", 5),
                        "urgency": item.get("urgency", 5),
                        "efforts": item.get("efforts", 5),
                        "reason": item.get("reason", "No reason provided")
                    }
            return {"evaluations": formatted_evals, "new_tasks": []}
            
        return data

    except Exception as e:
        print(f"Error parsing AI response: {e}")
        return {"evaluations": {}, "new_tasks": []}