# Parks Tech USA Daily Brief

A personal AI-powered newsletter that runs every morning at 6 AM, collects the top news across AI, Startups/Jobs, and US Immigration, and emails a curated digest to all subscribers.

---

## What It Does

Every morning the system:
1. Scrapes 10+ news sources across 3 categories
2. An AI agent ranks and picks the best stories
3. Composes a clean branded HTML email
4. Sends it to all subscribers from `newsletter@parkstechusa.com`

**Newsletter structure:**
- 🤖 AI News — Top 10
- 🚀 Startups & Jobs — Top 10
- 🇺🇸 US Immigration — Top 5

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **AI Agent** | OpenRouter + Llama 3.3 70b | Orchestrates the pipeline via tool calls |
| **News Sources** | Hacker News API, NewsAPI, RSS feeds, Dev.to API, arXiv API | Fetches raw articles |
| **Email Sending** | Resend | Delivers newsletter from `newsletter@parkstechusa.com` |
| **Domain** | parkstechusa.com (Namecheap) | Custom domain for professional email sending |
| **Subscribers** | SQLite (local) / ENV var (CI/CD) | Stores subscriber list |
| **Scheduler** | GitHub Actions (cron) | Triggers pipeline daily at 6 AM EST |
| **Language** | Python 3.11+ | Everything |

---

## News Sources

| Source | Category | API Key Required |
|---|---|---|
| Hacker News API | AI, Startup/Jobs | No |
| RSS Feeds (TechCrunch, VentureBeat, Wired, Verge, MIT Tech Review, Hugging Face, OpenAI blog) | AI | No |
| RSS Feeds (TechCrunch Startups, Crunchbase, Product Hunt, Remotive) | Startup/Jobs | No |
| RSS Feeds (USCIS, The Hill, NPR, Reuters, Politico, NBC, ABC) | Immigration | No |
| Dev.to API | AI, Startup/Jobs | No |
| arXiv API | AI Research | No |
| NewsAPI | All categories | Yes |

---

## How the Agent Works

The AI agent uses **tool calls** to run the pipeline. Instead of the LLM generating the newsletter itself, it acts as an orchestrator — calling Python functions in sequence:

```
System Prompt (prompts.py)
  └── tells the agent what to do and in what order

Agent Loop (agent.py)
  └── sends messages to OpenRouter API
  └── receives tool call instructions from the LLM
  └── executes the tool → sends result back to LLM
  └── repeats until done

Tools (tools.py)
  ├── get_top_news(category, count)      → fetches + ranks articles
  ├── compose_newsletter()               → builds HTML + plain text email
  ├── get_subscribers()                  → reads subscriber list
  └── send_newsletter(subject, recipients) → sends via Resend

State (_state dict in tools.py)
  └── articles are stored server-side between tool calls
  └── LLM never passes large data — just calls tools in order
```

---

## Project Structure

```
Parks News Letter/
├── .github/
│   └── workflows/
│       └── newsletter.yml      # GitHub Actions daily trigger
├── agent/
│   ├── agent.py                # Main agent loop
│   ├── tools.py                # Tool definitions + implementations
│   └── prompts.py              # System prompt for the LLM
├── sources/
│   ├── hackernews.py           # Hacker News API
│   ├── newsapi.py              # NewsAPI
│   ├── rss_feeds.py            # RSS feeds (TechCrunch, USCIS, etc.)
│   ├── devto.py                # Dev.to API
│   └── arxiv.py                # arXiv research papers
├── mailer/
│   ├── sender.py               # Resend + SMTP fallback
│   └── templates.py            # HTML + plain text email template
├── subscribers/
│   └── db.py                   # SQLite subscriber management
├── main.py                     # Entry point
├── manage.py                   # Subscriber CLI
├── scheduler.py                # Local APScheduler (alternative to CI/CD)
├── config.py                   # Loads all env vars
├── requirements.txt
└── .env                        # API keys (never committed)
```

---

## Setup

### 1. Clone and install

```bash
git clone https://github.com/yourusername/parks-news-letter.git
cd "Parks News Letter"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

Copy `.env` and fill in your keys:

```env
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct

NEWSAPI_KEY=your_newsapi_key

RESEND_API_KEY=re_...
FROM_EMAIL=newsletter@parkstechusa.com
FROM_NAME=Parks Tech USA
```

### 3. Add subscribers

```bash
python manage.py subscribe you@gmail.com --name "Your Name"
python manage.py list
python manage.py unsubscribe you@gmail.com
```

### 4. Run

```bash
# Test without sending email
python main.py --dry-run

# Send for real
python main.py

# Run on a schedule locally (7 AM daily)
python scheduler.py
```

---

## CI/CD — GitHub Actions

The newsletter runs automatically every morning at **6 AM EST** via GitHub Actions with no server required.

### Setup

1. Push the repo to GitHub
2. Go to **Settings → Secrets and variables → Actions**
3. Add these secrets:

| Secret | Value |
|---|---|
| `OPENROUTER_API_KEY` | Your OpenRouter key |
| `OPENROUTER_MODEL` | `meta-llama/llama-3.3-70b-instruct` |
| `NEWSAPI_KEY` | Your NewsAPI key |
| `RESEND_API_KEY` | Your Resend key |
| `FROM_EMAIL` | `newsletter@parkstechusa.com` |
| `FROM_NAME` | `Parks Tech USA` |
| `SUBSCRIBERS` | `email1@gmail.com,email2@gmail.com` |

### Manual trigger

Go to **Actions → Parks Tech USA Daily Newsletter → Run workflow** to fire it immediately.

---

## Domain & Email Setup

- Domain: `parkstechusa.com` registered on Namecheap
- Email sending: Resend with DNS verified via DKIM, SPF, and DMARC records
- Emails land in inbox (not spam) because the domain is properly authenticated

---

## Adding More Subscribers

Currently managed via CLI. Future plan: add a subscribe form on `parkstechusa.com`.

```bash
python manage.py subscribe friend@email.com --name "Friend"
```

---

## Built By

Parks RPK — [parkstechusa.com](https://parkstechusa.com)
