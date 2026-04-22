import os
import json
import google.genai as genai
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
AI_TOKEN = os.getenv("AI_TOKEN")
DATABASE_ID = os.getenv("DATABASE_ID")
CONTEXT_FILE = os.getenv("CONTEXT_FILE")

notion = Client(auth=NOTION_TOKEN)
ai_client = genai.Client(api_key=AI_TOKEN)


def load_context(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""


def fetch_tasks(filter_dict):
    response = notion.data_sources.query(
        **{"data_source_id": DATABASE_ID, "filter": filter_dict}
    )
    raw_results = response.get("results", [])
    clean_tasks = []
    for page in raw_results:
        properties = page["properties"]

        name_list = properties.get("Name", {}).get("title", [])
        name = name_list[0].get("plain_text", "Untitled") if name_list else "Untitled"

        desc_list = properties.get("Description", {}).get("rich_text", [])
        description = desc_list[0].get("plain_text", "") if desc_list else ""

        efforts = properties.get("Efforts", {}).get("number")
        efforts = efforts if efforts is not None else 0

        clean_tasks.append(
            {"id": page["id"], "name": name, "desc": description, "efforts": efforts}
        )
    return clean_tasks


def get_ai_response(to_process, done, pending, context):
    tasks_string = ""
    for i, t in enumerate(to_process):
        tasks_string += f"{i}. Name: {t['name']}\n   Description: {t['desc']}\n\n"

    done_str = "\n".join(
        [f"- {t['name']} (Efforts: {t['efforts']})" for t in done[:40]]
    )
    pending_str = "\n".join(
        [f"- {t['name']} (Efforts: {t['efforts']})" for t in pending]
    )

    prompt = f"""
    {context}
    
    PERFORMANCE CONTEXT (For your analysis only):
    Tasks Done (Recent):
    {done_str if done_str else "None"}
    
    Pending Tasks (Not Started / In Progress):
    {pending_str if pending_str else "None"}
    
    NEW TASKS TO EVALUATE:
    {tasks_string if tasks_string else "None"}
    
    INSTRUCTIONS:
    1. If there are NEW TASKS TO EVALUATE, score them (1-10) for importance, urgency, and efforts. Write a brief 'reason'. Reason should include your opinion about this task (delegate/do/schedule/forget)
    2. Analyze my load. If you see a logical gap between my global goals and my completed/pending tasks, AND my pending tasks volume is manageable, you MAY suggest new tasks in 'new_tasks'. If I am overloaded or no new tasks are needed, leave 'new_tasks' empty [].

    Return answer strictly in JSON format:
    {{
      "evaluations": {{
        "0": {{"importance": 10, "urgency": 5, "efforts": 3, "reason": "..."}}
      }},
      "new_tasks": [
        {{
          "name": "...",
          "description": "...",
          "importance": 8,
          "urgency": 4,
          "efforts": 5,
          "reason": "..."
        }}
      ]
    }}
    """

    response = ai_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={"response_mime_type": "application/json"},
    )
    return json.loads(response.text)


def update_notion_task(page_id, eval_results):
    notion.pages.update(
        page_id=page_id,
        properties={
            "Importance": {"number": eval_results["importance"]},
            "Urgency": {"number": eval_results["urgency"]},
            "Efforts": {"number": eval_results["efforts"]},
            "AI_comment": {
                "rich_text": [{"text": {"content": eval_results.get("reason", "")}}]
            },
            "AI_status": {"select": {"name": "Processed"}},
        },
    )


def create_notion_task(task_data):
    notion.pages.create(
        parent={"database_id": DATABASE_ID},
        properties={
            "Name": {"title": [{"text": {"content": task_data["name"]}}]},
            "Description": {
                "rich_text": [{"text": {"content": task_data.get("description", "")}}]
            },
            "Importance": {"number": task_data["importance"]},
            "Urgency": {"number": task_data["urgency"]},
            "Efforts": {"number": task_data["efforts"]},
            "AI_comment": {
                "rich_text": [{"text": {"content": task_data.get("reason", "")}}]
            },
            "AI_status": {"select": {"name": "Processed"}},
            "Status": {"status": {"name": "Not started"}},
        },
    )


if __name__ == "__main__":
    context = load_context(CONTEXT_FILE)

    to_process = fetch_tasks(
        {"property": "AI_status", "select": {"equals": "To Process"}}
    )
    done_tasks = fetch_tasks({"property": "Status", "status": {"equals": "Done"}})
    pending_all = fetch_tasks(
        {"property": "Status", "status": {"does_not_equal": "Done"}}
    )

    to_process_ids = {t["id"] for t in to_process}
    pending_tasks = [t for t in pending_all if t["id"] not in to_process_ids]

    if not to_process and not pending_tasks and not done_tasks:
        pass

    try:
        ai_response = get_ai_response(to_process, done_tasks, pending_tasks, context)

        evaluations = ai_response.get("evaluations", {})
        for index_str, scores in evaluations.items():
            idx = int(index_str)
            if idx < len(to_process):
                task_id = to_process[idx]["id"]
                update_notion_task(task_id, scores)

        new_tasks = ai_response.get("new_tasks", [])
        for nt in new_tasks:
            create_notion_task(nt)

    except Exception as e:
        print(f"Error: {e}")
        pass
