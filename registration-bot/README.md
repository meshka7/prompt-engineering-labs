# Registration Bot

This project contains an AI-powered bot for handling registration flows.  
It is part of the **Prompt Engineering Labs** collection.

---

## 📌 Features
- Collects and validates user input (contract number, role, password, etc.).
- Supports fallback to human agent if validation fails.
- Modular design: each step in the flow is a separate linked task.
- At the end of the flow, the bot generates an **outcome file** with the collected data.

---

## 🚀 Getting Started

### 1. Clone the repo
```bash
git clone git@github.com:meshka7/prompt-engineering-labs.git
cd prompt-engineering-labs/registration-bot

2. Install dependencies
bash
pip install -r requirements.txt

3. Run the bot
bash
python main.py

⚙️ Project Structure
bash
registration-bot/
│
├─ main.py              # Entry point
├─ output.html          # Example HTML output
├─ outcome.json         # Example outcome file with collected data
├─ requirements.txt     # Python dependencies
└─ README.md            # This file

