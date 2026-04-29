# 🧠 AI Task Prioritizer (Notion + Gemini)

A micro Python tool that acts as your personal AI productivity assistant. It connects to your Notion To-Do list and uses Google's Gemini AI to dynamically re-evaluate your tasks based on current context, time, and previously completed work.

## ✨ Features
*   **Dynamic Re-evaluation:** Automatically recalculates `Importance`, `Urgency`, `Efforts`, and an overall `Score` for all pending tasks.
*   **AI Reasoning:** Leaves a tactical comment explaining *why* you should do a specific task right now.
*   **Smart Task Generation:** Can suggest and automatically create new tasks based on your current context and schedule.
*   **Rate-Limit Safe:** Includes delays to respect Notion API limits.
*   **Fully Automated:** Ready to be hosted for free via GitHub Actions.

## 🛠 Tech Stack
*   Python 3
*   `notion-client` (Notion API)
*   `google-genai` (Google Gemini 3 Flash Preview)

## 📦 Setup & Local Installation

1. **Clone the repo:**
   ```bash
   git clone https://github.com/N10b1um/NotionTaskPrioritizer.git
   cd NotionTaskPrioritizer
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configuration:**
   Create a `.env` file in the root directory and fill it with your credentials:
   ```env
   NOTION_TOKEN=your_secret_notion_integration_token
   DATABASE_ID=your_notion_database_id
   PARENT_ID=your_notion_database_id_for_new_tasks
   AI_TOKEN=your_google_gemini_api_key
   CONTEXT_FILE=context.txt
   ```
   *Note: Create a `context.txt` file locally to write down your biography, goals, and rules for the AI.*

4. **Run the script:**
   ```bash
   python main.py
   ```

## ☁️ Automating with GitHub Actions (Free Hosting)

You can use GitHub Actions to automatically run the script by schedule.

1. Go to your repository settings on GitHub: **Settings** -> **Secrets and variables** -> **Actions**.
2. Create the following **Repository secrets** (matching your local `.env`):
   *   `NOTION_TOKEN`
   *   `AI_TOKEN`
   *   `DATABASE_ID`
   *   `PARENT_ID`
   *   `MY_CONTEXT` *(Paste the exact text/biography from your local `context.txt` here)*
3. Create a `.github/workflows/ai-planner.yml` file in your repository with this configuration:

```yaml
name: AI Notion Planner

on:
  schedule:
    - cron: '0 5,17 * * *'
  workflow_dispatch:

jobs:
  run-ai-planner:
    runs-on: ubuntu-latest
    env: 
      TZ: Europe/Minsk #change to your timezone
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Create context file securely
        run: echo "${{ secrets.MY_CONTEXT }}" > context.txt

      - name: Run Python script
        env:
          NOTION_TOKEN: ${{ secrets.NOTION_TOKEN }}
          AI_TOKEN: ${{ secrets.AI_TOKEN }}
          DATABASE_ID: ${{ secrets.DATABASE_ID }}
          PARENT_ID: ${{ secrets.PARENT_ID }}
          CONTEXT_FILE: "context.txt"
        run: python main.py
```
## 📝 Notion Database Template

The easiest way to get started is to duplicate the ready-made Notion template into your workspace. 

👉 **[Get the Notion Template Here](https://paint-ptarmigan-22f.notion.site/35137d3dc5b78029a0bffd0c91c1fe43?v=35137d3dc5b781a7a96e000ce4b87ac0&source=copy_link)** 👈

Once duplicated, extract the `DATABASE_ID` from the URL of your new database (it's the long string of characters between the workspace name and the `?v=` part).
    
**⚠️ Important: After duplicating the database, click the ••• menu in the top right corner of the Notion page, go to Connections -> Connect to, and select your created Notion Integration. Otherwise, the API will return a "Database not found" error.**

**Manual Setup (Fallback):**
If you prefer to build it yourself, your Notion Database must have the exact following properties:
*   `Name` (Title)
*   `Description` (Rich text)
*   `Status` (Status: "Not started", "Done", etc.)
*   `Importance` (Number)
*   `Urgency` (Number)
*   `Efforts` (Number)
*   `Score` (Number)
*   `AI_comment` (Rich text)
*   `Deadline` (Date)
*   `Completion date` (Date)

## 👤 Author
Created by **N10b1um**. Feel free to reach out or follow my work:
*   **GitHub:** [@N10b1um](https://github.com/N10b1um)
*   **Telegram:** [@Niobium](https://t.me/niobium)

## 📜 License
MIT License. Feel free to use and modify for your own productivity system!
