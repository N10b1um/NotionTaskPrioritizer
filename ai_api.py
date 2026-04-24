import json
from datetime import datetime
import google.genai as genai
import config

ai_client = genai.Client(api_key=config.AI_TOKEN)

def evaluate_tasks(to_process: list, done: list, pending: list, context: str) -> dict:
    today = datetime.now().strftime("%Y-%m-%d")
    
    tasks_string = ""
    for i, t in enumerate(to_process):
        deadline_info = f" (Deadline: {t['deadline']})" if t.get('deadline') else ""
        tasks_string += f"{i}. Name: {t['name']}{deadline_info}\n   Description: {t['desc']}\n\n"

    done_str = "\n".join([f"- {t['name']} (Efforts: {t['efforts']}, Date: {t['completion_date']})" for t in done[:40]])
    pending_str = "\n".join([f"- {t['name']} (Efforts: {t['efforts']}, Deadline: {t['deadline']})" for t in pending])

    prompt = f"""
    {context}
    TODAY'S DATE: {today}

    PRIORITIZATION FORMULA:
    Priority = (Importance * 8) + (Urgency * 4) - Efforts + [Deadline Bonus]

    Tasks Done:
    {done_str if done_str else "None"}
    
    Pending Tasks:
    {pending_str if pending_str else "None"}
    
    NEW TASKS:
    {tasks_string if tasks_string else "None"}
    
    INSTRUCTIONS:
    1. Score NEW TASKS (1-10).
    2. Provide reason and action (delegate/do/schedule/forget).
    3. Suggest 1-2 'new_tasks' if capacity allows.
    4. Return JSON only.

    {{
      "evaluations": {{ "0": {{"importance": 10, "urgency": 5, "efforts": 3, "reason": "..."}} }},
      "new_tasks": [ {{"name": "..", "description": "..", "importance": 8, "urgency": 4, "efforts": 5, "reason": ".."}} ]
    }}
    """
    
    response = ai_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={"response_mime_type": "application/json"},
    )
    return json.loads(response.text)