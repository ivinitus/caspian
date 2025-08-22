# Caspian AI Assistant

Caspian is an AI assistant platform with RAG capabilities, featuring a Discord bot, and a web interface.

## Deployment

This application is designed to be deployed on a VM instance using Docker Compose. For detailed deployment instructions, see the [VM Deployment Guide](VM_DEPLOYMENT_GUIDE.md).

## Project Structure

- **Backend**: FastAPI application with RAG system and Discord bot integration
- **Frontend**: Web interface for interacting with the AI assistant
- **Database**: PostgreSQL with pgvector extension for embeddings storage
- **Monitoring**: Optional Prometheus and Grafana stack for system monitoring

## Key Features

- Conversation memory with long-term storage
- RAG capabilities for knowledge retrieval
- Discord bot integration
- Reminder management
- Calendar integration
- Mobile and desktop interfaces

## Development Setup

1. Clone the repository
2. Create a `.env` file with the required environment variables
3. Run `docker-compose up -d` to start the development environment

## License

[MIT License](LICENSE)

## Acknowledgements

- [Sentence Transformers](https://www.sbert.net/) for embeddings
- [FastAPI](https://fastapi.tiangolo.com/) for the backend framework
- [pgvector](https://github.com/pgvector/pgvector) for vector similarity search
