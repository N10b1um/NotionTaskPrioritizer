import config
import logging
from utils import load_context
from notion_api import fetch_tasks, update_task, create_task
from ai_api import evaluate_tasks

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def main():
    logger.info("Script started")
    context = load_context(config.CONTEXT_FILE)

    to_process = fetch_tasks({"property": "AI_status", "select": {"equals": "To Process"}})
    done_tasks = fetch_tasks({"property": "Status", "status": {"equals": "Done"}})
    pending_all = fetch_tasks({"property": "Status", "status": {"does_not_equal": "Done"}})

    to_process_ids = {t["id"] for t in to_process}
    pending_tasks = [t for t in pending_all if t["id"] not in to_process_ids]

    if not to_process and not pending_tasks and not done_tasks:
        logger.info("No tasks to process")
        return

    try:
        logger.info(f"Evaluating {len(to_process)} tasks...")
        ai_response = evaluate_tasks(to_process, done_tasks, pending_tasks, context)

        evaluations = ai_response.get("evaluations", {})
        for idx_str, scores in evaluations.items():
            idx = int(idx_str)
            if idx < len(to_process):
                update_task(to_process[idx]["id"], scores)
                logger.info(f"Updated: {to_process[idx]['name']}")

        new_tasks = ai_response.get("new_tasks", [])
        for nt in new_tasks:
            create_task(nt)
            logger.info(f"Created new task: {nt.get('name')}")

    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    main()