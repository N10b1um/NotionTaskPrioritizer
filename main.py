import time
import logging
import config
from utils import load_context
from notion_api import fetch_tasks, update_task, create_task
from ai_api import evaluate_tasks

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def main():
    logger.info("Script started")
    
    try:
        context = load_context(config.CONTEXT_FILE)
    except Exception as e:
        logger.exception("Failed to load context file")
        return

    try:
        pending_tasks = fetch_tasks({"property": "Status", "status": {"does_not_equal": "Done"}})
        done_tasks = fetch_tasks({"property": "Status", "status": {"equals": "Done"}})
    except Exception as e:
        logger.exception("Failed to fetch tasks from Notion")
        return

    if not pending_tasks:
        logger.info("No active tasks to evaluate.")
        return

    logger.info(f"Sending {len(pending_tasks)} tasks to AI for re-evaluation...")
    
    try:
        ai_response = evaluate_tasks(pending_tasks, done_tasks, context)
        evaluations = ai_response.get("evaluations", {})
        new_tasks = ai_response.get("new_tasks", [])
        
        update_count = 0
        for task_id, scores in evaluations.items():
            try:
                update_task(task_id, scores)
                update_count += 1
                time.sleep(0.3)
            except Exception as e:
                logger.warning(f"Failed to update task {task_id}: {e}")

        logger.info(f"Successfully updated priorities for {update_count}/{len(evaluations)} tasks.")

        for nt in new_tasks:
            try:
                create_task(nt)
                logger.info(f"Created new task from AI: {nt.get('name')}")
                time.sleep(0.3)
            except Exception as e:
                logger.warning(f"Failed to create new task '{nt.get('name')}': {e}")

    except Exception as e:
        logger.exception("Critical Error during AI evaluation process")

if __name__ == "__main__":
    main()