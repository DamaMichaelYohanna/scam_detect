# Telegram Anti-Scam Bot (FastAPI + Exa.ai + OpenAI)

A high-performance FastAPI backend for a Telegram group bot that protects community members from scams, phishing, and wallet drainers by leveraging **Exa.ai** for real-time web content verification and **OpenAI (GPT-4o/mini)** for structured threat analysis.

---

## 🌟 How It Works

1. **Telegram Webhook Ingestion**: Receives incoming group messages via `/webhook/telegram` and verifies the Telegram secret token.
2. **Instant 200 OK**: Dispatches detection tasks asynchronously to background workers to prevent webhook timeouts.
3. **Smart Heuristic Pre-filter**: Instantly extracts URLs, crypto addresses (ETH, SOL, BTC), and high-risk trigger keywords (*airdrop*, *free mint*, *connect wallet*, *dm admin*, etc.). Safe conversations bypass deep scans to save API costs.
4. **Live Web Intelligence (Exa.ai)**:
   - Fetches live page title, DOM text, and summaries for suspicious links.
   - Searches the web for real-time domain reputation and scam/hack reports.
5. **Structured Threat Evaluation (OpenAI)**: Evaluates the message and Exa web context against known phishing vectors, wallet drainers, and social engineering attacks.
6. **Automated Group Warning**: When a scam is identified above the confidence threshold (e.g., $\ge 70\%$), the bot replies directly to the offending message in the Telegram group with a clear warning card and safety advice.

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
