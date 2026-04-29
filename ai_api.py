import json
from datetime import datetime
import google.genai as genai
import config

ai_client = genai.Client(api_key=config.AI_TOKEN)

def evaluate_tasks(pending: list, done: list, context: str) -> dict:
    today = datetime.now().strftime("%Y-%m-%d")
    
    pending_str = ""
    for t in pending:
        dead_str = f", Deadline: {t['deadline']}" if t['deadline'] else ""
        pending_str += f"- ID: {t['id']}\n  Name: {t['name']}\n  Current Efforts: {t['efforts']}{dead_str}\n  Desc: {t['desc']}\n\n"

    done_str = "\n".join([f"- {t['name']} (Date: {t['completion_date']})" for t in done[:20]])

    prompt = f"""
    {context}
    TODAY'S DATE: {today}

    PRIORITIZATION FORMULA:
    Priority = (Importance * 8) + (Urgency * 4) - Efforts + [Deadline Bonus]

    CONTEXT (Recently Done Tasks):
    {done_str if done_str else "None"}
    
    ALL PENDING TASKS (Needs Holistic Re-evaluation):
    {pending_str if pending_str else "None"}
    
    INSTRUCTIONS:
    1. You MUST re-evaluate ALL pending tasks holistically. Look at the entire board.
    2. Adjust 'importance' and 'urgency' (1-10) for EACH task based on Today's Date. If deadlines are approaching, urgency must go up. If new tasks are more critical, lower the importance of older, less critical tasks to "make room".
    3. Be strict. Not everything can be importance 10. Force a spread of priorities.
    4. Provide a very short 'reason' (max 1 sentence) for the new scores.
    5. Suggest 1 'new_tasks' ONLY if there is a logical gap or capacity allows.
    6. STRICTLY use the exact Notion Task "ID" as the key in the "evaluations" JSON object.
    
    Return answer strictly in JSON format:
    {{
      "evaluations": {{
        "ID_FROM_PROMPT_HERE": {{"importance": 9, "urgency": 8, "efforts": 3, "reason": "Deadline is tomorrow, priority increased."}},
        "ANOTHER_ID_HERE": {{"importance": 4, "urgency": 2, "efforts": 5, "reason": "Pushed back to focus on more urgent tasks."}}
      }},
      "new_tasks": [
        {{"name": "..", "description": "..", "importance": 8, "urgency": 4, "efforts": 5, "reason": ".."}}
      ]
    }}
    """
    
    response = ai_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={"response_mime_type": "application/json"},
    )
    return json.loads(response.text)