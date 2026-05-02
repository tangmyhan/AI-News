# AI-News Dashboard

**AI-News Dashboard** is an automated, real-time intelligence system built for enterprises (specifically in the Logistics and Energy sectors). It aggregates news from major Vietnamese publishers, analyzes them using Large Language Models (LLMs), and evaluates the business impact (Positive/Negative/Neutral) along with relevance scores.

## 🚀 Key Features
- **Automated Data Ingestion**: Periodically scrapes and parses RSS feeds and web pages from Tuổi Trẻ and VnExpress.
- **Deduplication**: Prevents redundant processing by checking existing articles through Redis cache.
- **AI-Powered NLP Pipeline**: Leverages OpenAI to summarize articles, extract key entities, and determine the business impact specifically tailored to the Logistics & Energy domains.
- **Real-Time Dashboard**: An elegant, glassmorphism-styled Vanilla HTML/CSS/JS frontend providing quick statistical overviews, impact distribution charts, and a full-text search interface.
- **Robust Full-Text Search**: Powered by PostgreSQL GIN Index to efficiently search through thousands of Vietnamese articles.

## 🛠 Tech Stack
- **Backend API**: Python 3, FastAPI, Uvicorn, SQLAlchemy
- **Data Pipeline & Workers**: Celery, Celery Beat, Redis (Broker/Backend)
- **Database**: PostgreSQL (with JSONB and GIN indexes)
- **AI / NLP**: LangChain, OpenAI (`gpt-4o-mini`)
- **Frontend**: Vanilla HTML5, CSS3, JavaScript, Chart.js (CDN)
- **Web Scraping**: BeautifulSoup4, Feedparser, Requests

---

## 📂 Project Structure

```text
.
├── api/                   # RESTful API built with FastAPI
│   ├── main.py            # API routing, stats endpoints, and static file serving
│   └── requirements.txt   # API specific dependencies
├── database/              # DB connection and ORM schemas
│   ├── db_client.py       # PostgreSQL SQLAlchemy engine initialization
│   └── models.py          # SQLAlchemy Article model (maps to 'articles' table)
├── docker-compose.yml     # Docker definitions for PostgreSQL & Redis
├── frontend/              # Frontend UI components
│   ├── index.html         # Main dashboard markup
│   ├── styles.css         # Custom styling (Glassmorphism, Dark mode)
│   └── app.js             # Logic for fetching API, rendering charts and lists
├── ingestion/             # Web Crawlers and data ingestion scripts
│   ├── filter.py          # Deduplication logic using Redis
│   ├── producer.py        # Master script calling spiders sequentially
│   ├── tuoitre_spider.py  # Tuoi Tre RSS & HTML scraper
│   └── vnexpress_spider.py# VnExpress RSS & HTML scraper
├── processing/            # AI analysis and Celery worker definitions
│   ├── nlp_service.py     # LangChain OpenAI prompt chains & text processing
│   └── worker.py          # Celery worker tasks that invoke nlp_service
├── shared/                # Configurations shared across the system
│   ├── celery_app.py      # Celery app & beat schedule configurations
│   ├── config.py          # Environment variable loaders
│   └── logger.py          # Unified logging configurations
└── requirements.txt       # Global Python dependencies for the project
```

---

## 🚦 Getting Started (Local Development)

Follow these steps to build and run the application from scratch.

### 1. Prerequisites
- **Python 3.10+**
- **Docker & Docker Compose** (for Redis and Postgres)
- **Git**

### 2. Environment Variables
Create a `.env` file in the root directory (and `/processing/.env` if needed) with the following content:

```env
OPENAI_API_KEY=your_openai_api_key_here
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=ainews
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
REDIS_URL=redis://localhost:6379/0
```

### 3. Start Infrastructure Services
Start the PostgreSQL database and Redis server using Docker Compose:

```bash
docker-compose up -d
```

### 4. Install Dependencies
Create a virtual environment and install the required Python packages:

```bash
# Windows
python -m venv myenv
myenv\Scripts\activate

# Linux/Mac
python3 -m venv myenv
source myenv/bin/activate

pip install -r requirements.txt
```

### 5. Start the FastAPI Server
The API backend also serves the frontend dashboard files.

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```
*You can now access the dashboard at: `http://localhost:8000/dashboard/`*

### 6. Start Celery Worker (Processing)
Open a new terminal, activate the virtual environment, and run the Celery worker to consume processing tasks (AI Analysis):

```bash
# On Windows, use gevent pool
celery -A shared.celery_app worker --loglevel=info -P gevent

# On Linux/Mac
celery -A shared.celery_app worker --loglevel=info
```

### 7. Start Celery Beat (Scheduled Ingestion)
Open another terminal, activate the virtual environment, and start the scheduler. This will automatically trigger `producer.py` every hour to fetch new articles:

```bash
celery -A shared.celery_app beat --loglevel=info
```

*(Optional) You can manually test the ingestion pipeline without waiting for the schedule by running:*
```bash
python ingestion/producer.py
```

---