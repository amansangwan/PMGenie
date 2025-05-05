# 🤖 PMGenie – AI Jira Agent

PMGenie is a powerful AI agent built to automate project management tasks like Jira summarization, risk analysis, task prioritization, and PDF reporting.

## 🔧 Features

- GPT-based structured reasoning (`START`, `PLAN`, `ACTION`, `OBSERVATION`, `OUTPUT`)
- Tool integration: Jira, PDF, task manager
- Beautiful PDF reports (Jinja2 + WeasyPrint)
- Scalable and modular design

## 🚀 Getting Started

```bash
git clone https://github.com/amansangwan/PMGenie.git
cd PMGenie
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
