from notion_client import Client
import config

notion = Client(auth=config.NOTION_TOKEN)

def fetch_tasks(filter_dict: dict) -> list:
    response = notion.data_sources.query(
        data_source_id=config.DATABASE_ID, 
        filter=filter_dict
    )
    raw_results = response.get("results", [])
    
    clean_tasks = []
    for item in raw_results:
        properties = item.get("properties", {})

        name_prop = properties.get("Name") or {}
        name_list = name_prop.get("title", [])
        name = name_list[0].get("plain_text", "Untitled") if name_list else "Untitled"

        desc_prop = properties.get("Description") or {}
        desc_list = desc_prop.get("rich_text", [])
        description = desc_list[0].get("plain_text", "") if desc_list else ""

        efforts = (properties.get("Efforts") or {}).get("number") or 0
        
        comp_prop = properties.get("Completion date") or {}
        comp_date_obj = comp_prop.get("date") or {}
        comp_date = comp_date_obj.get("start", "") if comp_date_obj else ""
        
        dead_prop = properties.get("Deadline") or {}
        dead_date_obj = dead_prop.get("date") or {}
        deadline = dead_date_obj.get("start", "") if dead_date_obj else ""

        clean_tasks.append({
            "id": item["id"], 
            "name": name, 
            "desc": description, 
            "efforts": efforts, 
            "completion_date": comp_date, 
            "deadline": deadline
        })
    return clean_tasks

def update_task(page_id: str, eval_results: dict):
    notion.pages.update(
        page_id=page_id,
        properties={
            "Importance": {"number": eval_results.get("importance", 0)},
            "Urgency": {"number": eval_results.get("urgency", 0)},
            "Efforts": {"number": eval_results.get("efforts", 0)},
            "AI_comment": {"rich_text": [{"text": {"content": eval_results.get("reason", "")}}]},
            "AI_status": {"select": {"name": "Processed"}},
        },
    )

def create_task(task_data: dict):
    notion.pages.create(
        parent={"database_id": config.PARENT_ID}, 
        properties={
            "Name": {"title": [{"text": {"content": task_data.get("name", "New Task")}}]},
            "Description": {"rich_text": [{"text": {"content": task_data.get("description", "")}}]},
            "Importance": {"number": task_data.get("importance", 0)},
            "Urgency": {"number": task_data.get("urgency", 0)},
            "Efforts": {"number": task_data.get("efforts", 0)},
            "AI_comment": {"rich_text": [{"text": {"content": task_data.get("reason", "")}}]},
            "AI_status": {"select": {"name": "Processed"}},
            "Status": {"status": {"name": "Not started"}},
        },
    )