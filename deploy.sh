#!/bin/bash
# Caspian VM Deployment Script

# Exit on error
set -e

# Update from git repository
echo "Pulling latest changes..."
git pull

# Build and restart containers
echo "Building and restarting containers..."
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Create a database backup before migrations
echo "Creating database backup..."
BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
docker-compose exec -T postgres pg_dump -U caspian_user caspian_db > ./db-backups/$BACKUP_FILE

# Run database migrations if needed
echo "Running database migrations..."
docker-compose exec -T backend python -m app.scripts.setup_db

# Check container status
echo "Checking container status..."
docker-compose ps

echo "Deployment completed successfully!"
echo "Backup created at ./db-backups/$BACKUP_FILE"

# Optional: Send notification about successful deployment
# curl -X POST -H "Content-Type: application/json" -d '{"text":"Caspian deployment successful!"}' YOUR_WEBHOOK_URL
curl -X POST -H "Content-Type: application/json" \
-d '{"Content":" @vinitus Caspian deployment successful!"}' \
https://hooks.chime.aws/incomingwebhooks/67239532-c7db-418c-a5dc-a9c7c1a29f93?token=alBJSDA1N3l8MXx0dEpDWnZWZ2pZdDBKUDRGeXVwVUk1RFBiNXZrVE9IUXZQbUdQY0VMb2t3

