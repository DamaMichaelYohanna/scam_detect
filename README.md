# 🛡️ Yeittu Sentinel: Telegram Anti-Scam Agent

A real-time ambient AI agent built for Telegram communities that detects scams, phishing links, and wallet drainers by leveraging **Exa.ai** for live web verification and **OpenAI (GPT-4o-mini)** / **Google Gemini (Gemini 3.6-flash)** for structured threat reasoning.

Built for the **[AI Tinkerers Hackathon - Agents, Everywhere (Abuja)](https://abuja.aitinkerers.org/hackathons/h_g9To6f0UerQ)**.  
📖 Read the full **[Hackathon Submission Document (SUBMISSION.md)](SUBMISSION.md)**.

---

## 🌟 Key Highlights & Moderation Policy

1. **Ambient Stream Monitoring**: Intercepts Telegram messages in real time without requiring manual invocations.
2. **Exa.ai Live Web Intelligence**: Reads live webpage content (`get_contents`) and checks domain reputation (`search_and_contents`).
3. **Multi-Model Cognitive Engine**: Hot-swap between **Google Gemini 3.6-flash** and **OpenAI GPT-4o-mini** with structured outputs.
4. **5-Strike Escalation System**:
   - **Strike 1 & 2**: Immediate malicious message deletion + safety explanation card.
   - **Strike 3 & 4**: Message deleted + **Public Strike Warning (3/5)**.
   - **Strike 5**: Message deleted + **Automatic User Ban & Removal** from the group.

---

## 📁 Project Structure

```
yeittubot/
├── app/
│   ├── main.py                     # FastAPI application & lifespan events
│   ├── config.py                   # Pydantic settings & environment variables
│   ├── models/
│   │   └── scam_models.py          # Unified Pydantic schema for threat results
│   ├── routers/
│   │   └── webhook.py              # Webhook endpoint & background task runner
│   └── services/
│       ├── analyzer_service.py     # Multi-provider AI manager (OpenAI <-> Gemini)
│       ├── detector_service.py     # Regex & heuristic detection
│       ├── exa_service.py          # Exa.ai live web crawling & intelligence
│       ├── gemini_service.py       # Google Gemini threat analysis
│       ├── openai_service.py       # OpenAI threat analysis
│       ├── poller_service.py       # Direct Telegram long-polling service
│       └── telegram_service.py     # Telegram Bot API client & warning formatters
├── test_pipeline.py                # Standalone test runner for mock messages
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variable template
└── README.md                       # Documentation
```

---

## 🚀 Quickstart Guide

### 1. Configure Environment Variables
Edit [`.env`](file:///c:/Users/HomePC/yeittubot/.env):

```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=8946767047:AAGkNfp-Z5mrjFxRDS7BfHhkGgNzk6opnl0

# Exa.ai
EXA_API_KEY=your_exa_api_key

# 🧠 Select AI Provider ("openai" or "gemini")
AI_PROVIDER=openai

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini

# Google Gemini Configuration
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash

# Polling vs Webhook
POLLING_MODE=true
```

---

### 2. Configure Telegram Bot Permissions
To allow your bot to read all group messages:
1. Open Telegram and search for [@BotFather](https://t.me/BotFather).
2. Send `/setprivacy`.
3. Select your bot.
4. Set it to **Disable** (or alternatively, make the bot an **Admin** in your group).

---

### 3. Start the FastAPI Server
Run the FastAPI development server:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive API documentation will be available at [http://localhost:8000/docs](http://localhost:8000/docs).

---

### 4. Setting up the Webhook

#### Using ngrok (for local development):
1. Start ngrok tunnel:
   ```bash
   ngrok http 8000
   ```
2. Copy your public HTTPS URL (e.g. `https://abc-123.ngrok-free.app`).
3. Set `WEBHOOK_URL` in `.env` or register the webhook via the API:
   ```bash
   curl -X POST "http://localhost:8000/webhook/setup?webhook_url=https://abc-123.ngrok-free.app"
   ```
4. Verify webhook status anytime:
   ```bash
   curl -X GET "http://localhost:8000/webhook/info"
   ```

---

## 🧪 Testing

Run the local test pipeline to verify heuristic detection without live webhooks:

```bash
python test_pipeline.py
```
