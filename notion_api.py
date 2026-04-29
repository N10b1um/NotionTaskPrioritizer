from typing import List, Dict, Any
from notion_client import Client
import config

notion = Client(auth=config.NOTION_TOKEN)

def _get_text(properties: Dict[str, Any], prop_name: str) -> str:
    prop = properties.get(prop_name) or {}
    text_list = prop.get("title") or prop.get("rich_text") or []
    return text_list[0].get("plain_text", "") if text_list else ""

def _get_num(properties: Dict[str, Any], prop_name: str) -> float:
    return float((properties.get(prop_name) or {}).get("number") or 0.0)

def fetch_tasks(filter_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
    response = notion.data_sources.query(
        data_source_id=config.DATABASE_ID, 
        filter=filter_dict
    )
    
    clean_tasks = []
    for item in response.get("results", []):
        properties = item.get("properties", {})
        
        comp_prop = properties.get("Completion date") or {}
        comp_date = (comp_prop.get("date") or {}).get("start", "")
        
        dead_prop = properties.get("Deadline") or {}
        deadline = (dead_prop.get("date") or {}).get("start", "")

        clean_tasks.append({
            "id": item["id"], 
            "name": _get_text(properties, "Name"), 
            "desc": _get_text(properties, "Description"),
            "ai_comment": _get_text(properties, "AI_comment"),
            "efforts": _get_num(properties, "Efforts"), 
            "importance": _get_num(properties, "Importance"),
            "urgency": _get_num(properties, "Urgency"),
            "score": _get_num(properties, "Score"),
            "completion_date": comp_date, 
            "deadline": deadline
        })
    return clean_tasks

def update_task(page_id: str, scores: Dict[str, Any]) -> None:
    notion.pages.update(
        page_id=page_id,
        properties={
            "Score": {"number": float(scores.get("score", 0))},
            "Importance": {"number": float(scores.get("importance", 0))},
            "Urgency": {"number": float(scores.get("urgency", 0))},
            "Efforts": {"number": float(scores.get("efforts", 0))},
            "AI_comment": {"rich_text": [{"text": {"content": str(scores.get("reason", ""))}}]},
            "AI_status": {"select": {"name": "Processed"}},
        },
    )

def create_task(task_data: Dict[str, Any]) -> None:
    notion.pages.create(
        parent={"database_id": config.PARENT_ID}, 
        properties={
            "Name": {"title": [{"text": {"content": task_data.get("name", "New Task")}}]},
            "Description": {"rich_text": [{"text": {"content": task_data.get("description", "")}}]},
            "Importance": {"number": float(task_data.get("importance", 0))},
            "Urgency": {"number": float(task_data.get("urgency", 0))},
            "Efforts": {"number": float(task_data.get("efforts", 0))},
            "Score": {"number": float(task_data.get("score", 0))},
            "AI_comment": {"rich_text": [{"text": {"content": task_data.get("reason", "")}}]},
            "AI_status": {"select": {"name": "Processed"}},
            "Status": {"status": {"name": "Not started"}},
        },
    )