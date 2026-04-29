import json
import logging
from datetime import datetime
from typing import List, Dict, Any
import google.genai as genai
import config

logger = logging.getLogger(__name__)
ai_client = genai.Client(api_key=config.AI_TOKEN)

def _format_pending_task(t: Dict[str, Any]) -> str:
    """Formats a single task for the AI prompt."""
    dead_str = f" | Deadline: {t['deadline']}" if t.get('deadline') else ""
    metrics = f"Imp: {t['importance']}, Urg: {t['urgency']}, Score: {t['score']}, Efforts: {t['efforts']}"
    
    parts = [
        f"- ID: {t['id']}",
        f"  Name: {t['name']}",
        f"  Desc: {t['desc']}",
        f"  Current State: {metrics}{dead_str}"
    ]
    if t.get('ai_comment'):
        parts.append(f"  Last AI advice: {t['ai_comment']}")
    
    return "\n".join(parts) + "\n\n"

def _normalize_keys(data: Dict[str, Any]) -> Dict[str, Any]:
    """Ensures all keys in the dictionary are lowercase for consistent processing."""
    return {k.lower(): v for k, v in data.items()}

def evaluate_tasks(pending: List[Dict[str, Any]], done: List[Dict[str, Any]], context: str) -> Dict[str, Any]:
    """Sends tasks to Gemini for re-evaluation and potential new task generation."""
    now = datetime.now()
    
    pending_str = "".join(_format_pending_task(t) for t in pending)
    done_str = "\n".join(f"- {t['name']}" for t in done[:15]) or "None"

    full_system_instruction = f"""
    {context}
    
    STRICT RESPONSE SCHEMA EXAMPLE:
    {{
      "evaluations": {{
        "34a37d3d-c5b7-8034-b9c2-d9386b6173d4": {{
          "importance": 10,
          "urgency": 8,
          "efforts": 5,
          "score": 95,
          "reason": "This is a Tier 1 task. Do it in the morning while your brain is fresh. Focus on the core logic."
        }}
      }},
      "new_tasks": [
        {{
          "name": "Vocabulary Review",
          "description": "30 words from the SAT list",
          "importance": 9,
          "urgency": 5,
          "efforts": 2,
          "score": 80,
          "reason": "Perfect for your commute. Use the resource from https://example.com"
        }}
      ]
    }}

    CRITICAL RULES:
    1. Return ONLY the JSON object. No extra text.
    2. Use the exact Notion IDs provided in the prompt as keys for "evaluations".
    3. The 'reason' field must be in English, tactical, and concise.
    """

    user_query = f"""
    CURRENT DATE: {now.strftime("%Y-%m-%d")} ({now.strftime("%A")}), TIME: {now.strftime("%H:%M")}
    RECENTLY COMPLETED TASKS:
    {done_str}
    
    TASKS TO EVALUATE:
    {pending_str}
    
    ACTION: Re-evaluate the tasks and return the JSON following the SCHEMA EXAMPLE.
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
        text = response.text.strip()
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            text = text[start:end+1]
        
        data = json.loads(text)
        
        if isinstance(data, dict):
            evals = {k: _normalize_keys(v) for k, v in data.get("evaluations", {}).items()}
            new_tasks = [_normalize_keys(t) for t in data.get("new_tasks", [])]
            return {"evaluations": evals, "new_tasks": new_tasks}
            
        return {"evaluations": {}, "new_tasks": []}

    except Exception as e:
        logger.exception("Error parsing AI response")
        logger.debug(f"Raw response: {response.text}")
        return {"evaluations": {}, "new_tasks": []}