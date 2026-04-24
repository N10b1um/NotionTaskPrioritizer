import os
from dotenv import load_dotenv

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
AI_TOKEN = os.getenv("AI_TOKEN")
DATABASE_ID = os.getenv("DATABASE_ID")
PARENT_ID = os.getenv("PARENT_ID")
CONTEXT_FILE = os.getenv("CONTEXT_FILE", "context.txt")