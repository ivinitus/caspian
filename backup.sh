#!/bin/bash
# Caspian Backup Script

# Set backup directory
BACKUP_DIR="./db-backups"
BACKUP_FILENAME="backup_$(date +%Y%m%d_%H%M%S).sql"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_FILENAME"

# Ensure backup directory exists
mkdir -p $BACKUP_DIR

# Create backup
echo "Creating database backup..."
docker-compose exec -T db pg_dump -U caspian_user caspian_db > $BACKUP_PATH

# Check if backup was successful
if [ $? -eq 0 ]; then
    echo "Backup created successfully at $BACKUP_PATH"
    
    # Compress backup
    gzip $BACKUP_PATH
    echo "Backup compressed to ${BACKUP_PATH}.gz"
    
    # Remove backups older than 30 days
    find $BACKUP_DIR -name "backup_*.sql.gz" -type f -mtime +30 -delete
    echo "Removed backups older than 30 days"
    
    # Optional: Upload to cloud storage
    # gsutil cp ${BACKUP_PATH}.gz gs://your-backup-bucket/
    # echo "Backup uploaded to cloud storage"
else
    echo "Backup failed!"
    exit 1
fi
