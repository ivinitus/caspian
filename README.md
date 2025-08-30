
# Caspian

## Overview

Caspian is a full-stack, modular AI assistant platform featuring:

- **FastAPI backend** with plugin architecture
- **Discord bot integration**
- **Reminders, scheduling, and RAG (Retrieval-Augmented Generation)**
- **Vector search** using PostgreSQL + pgvector
- **User authentication, preferences, and extensibility**
- **Modern frontend** (web, desktop, mobile)
- **Robust Docker, VM, and GCP deployment**
- **Automated CI/CD with Discord notifications**

---

## Features

- Modular FastAPI backend (Python 3.10+)
- Discord bot for chat, reminders, and automation
- RAG (Retrieval-Augmented Generation) with vector search
- Reminders, calendar, and scheduling
- Plugin system for custom automation and integrations
- User authentication, preferences, and roles
- PostgreSQL with pgvector for semantic search
- Modern frontend (Vite/React web, desktop, mobile)
- Docker Compose for local/dev deployment
- GCP/VM deployment scripts and guides
- Automated GitHub Actions CI/CD with Discord notifications

---

## Project Structure

```
caspian/
	backend/
		app/
			api/           # FastAPI endpoints (auth, conversation, plugins, etc.)
			core/          # Core logic (LLM, reminders, config, etc.)
			db/            # Database models
			plugins/       # Plugin system
			...
		scripts/         # Utility and setup scripts
		Dockerfile
		requirements.txt
		...
	frontend/
		web/             # Vite/React web app
		desktop/         # Electron desktop app
		mobile/          # React Native mobile app
		...
	infra/
		k8s/             # Kubernetes manifests
		...
	...
```

---

## Quickstart (Development)

### Prerequisites

- Docker & Docker Compose
- Python 3.10+
- Node.js (for frontend)

### 1. Clone the repository

```bash
git clone https://github.com/ivinitus/caspian
cd caspian
```

### 2. Configure environment variables

Copy `.env.example` to `.env` in `caspian/backend/` and fill in required values:

```bash
cp caspian/backend/.env.example caspian/backend/.env
# Edit caspian/backend/.env as needed
```

### 3. Start services with Docker Compose

```bash
docker-compose up --build
```

### 4. Access the app

- Backend API: http://localhost:8000
- Frontend (web): http://localhost:5173

### 5. (Optional) Run database setup scripts

```bash
# if using setup_db.py or Alembic)
docker-compose exec backend python scripts/setup_db.py

```

---

## Environment Variables

All required variables are documented in `caspian/backend/.env.example`. Key variables include:

- `DATABASE_URL` - PostgreSQL connection string (with pgvector)
- `DISCORD_TOKEN` - Discord bot token
- `SECRET_KEY` - App secret key
- `CORS_ORIGINS` - JSON list of allowed origins (e.g., '["http://localhost:5173"]')
- `OPENAI_API_KEY` - (if using OpenAI)
- `DEFAULT_USER_EMAIL`, `DEFAULT_USER_PASSWORD` - Initial admin user

**Note:** The backend will fail to start if any required variable is missing or empty.

---

## Deployment

### Docker Compose (Recommended for Dev)

```bash
docker-compose up --build -d
```


### GCP/VM Deployment

For GCP/VM deployment instructions, see the deployment section in this README or consult your team documentation.

### GitHub Actions CI/CD

- Automated deployment to GCP
- Discord notifications on deployment status
- All secrets managed via GitHub Actions/Secrets

---

## Database

- **PostgreSQL** with **pgvector** extension is required for vector search.
- The backend checks and installs pgvector on startup if missing.
- See `init-vector.sql` for extension setup.

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request (PR)

---

## License

See the `LICENSE` file for details.

---


## Contact & Support

- For issues, open a GitHub issue or discussion
- For deployment help, refer to the deployment section above or ask in the repository discussions.

---
