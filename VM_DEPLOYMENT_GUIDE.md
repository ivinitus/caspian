
# Caspian VM Deployment Guide

This is the official guide for deploying the **Caspian AI Assistant** platform on your own VM instance (Google Cloud Platform or any other provider).

---


## Why Deploy Caspian on a VM?

VM-based deployment offers:
- **Consistent performance** for AI/ML workloads (no cold starts)
- **Predictable costs** for steady workloads
- **Full control** over your environment and security
- **All-in-one architecture** (backend, frontend, database, vector search)
- **Best for AI processing** (dedicated resources for LLMs, vector embeddings)

## 1. Create and Configure Your VM

1. **Create a VM (example: Google Cloud):**
    ```bash
    gcloud compute instances create caspian-server \
       --zone=us-central1-a \
       --machine-type=e2-standard-4 \
       --boot-disk-size=50GB \
       --image-family=ubuntu-2004-lts \
       --image-project=ubuntu-os-cloud \
       --tags=http-server,https-server
    ```

2. **Open firewall ports:**
    ```bash
    gcloud compute firewall-rules create allow-http \
       --allow tcp:80 \
       --target-tags http-server
    gcloud compute firewall-rules create allow-https \
       --allow tcp:443 \
       --target-tags https-server
    ```

3. **SSH into your VM:**
    ```bash
    gcloud compute ssh caspian-server --zone=us-central1-a
    ```

## 2. Install Docker & Docker Compose

1. **Update packages and install dependencies:**
   ```bash
   sudo apt update
   sudo apt install -y apt-transport-https ca-certificates curl software-properties-common
   ```

2. **Install Docker:**
   ```bash
   # Add Docker's official GPG key
   curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

   # Set up the Docker repository
   echo \
     "deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
     $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

   # Install Docker
   sudo apt update
   sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

   # Add your user to the docker group
   sudo usermod -aG docker $USER
   ```

3. **Install Docker Compose (if not included):**
   ```bash
   sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

4. **Log out and back in for group changes:**
   ```bash
   exit
   gcloud compute ssh caspian-server --zone=us-central1-a
   ```

## 3. Set Up Caspian Project

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ivinitus/caspian.git
   cd caspian
   ```

2. **Create needed directories:**
   ```bash
   mkdir -p ssl nginx-logs db-backups
   ```

3. **Configure environment variables:**
   - Copy `.env.example` to `.env` in `caspian/backend/`:
     ```bash
     cp caspian/backend/.env.example caspian/backend/.env
     nano caspian/backend/.env
     ```
   - Fill in all required values. Key variables include:
     - `DATABASE_URL` (PostgreSQL connection string)
     - `DISCORD_TOKEN` (Discord bot token)
     - `SECRET_KEY` (App secret key)
     - `CORS_ORIGINS` (allowed origins)
     - `OPENAI_API_KEY` (if using OpenAI)
     - `DEFAULT_USER_EMAIL`, `DEFAULT_USER_PASSWORD` (admin user)
   - See `caspian/backend/.env.example` for all options.


## 4. Configure SSL/TLS with Certbot

1. **Install Certbot**:
   ```bash
   sudo apt install -y certbot
   ```

2. **Obtain SSL certificate**:
   ```bash
   sudo certbot certonly --standalone -d yourdomain.com -d api.yourdomain.com
   ```

3. **Copy certificates to Nginx**:
   ```bash
   sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ssl/
   sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ssl/
   sudo chown -R $USER:$USER ssl/
   ```

4. **Set up auto-renewal**:
   ```bash
   sudo crontab -e
   ```

   Add this line:
   ```
   0 3 * * * certbot renew --quiet && cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem /home/$(whoami)/caspian/ssl/ && cp /etc/letsencrypt/live/yourdomain.com/privkey.pem /home/$(whoami)/caspian/ssl/ && docker-compose restart frontend
   ```

## 5. Deploy Caspian

1. **Start all services with Docker Compose:**
   ```bash
   docker-compose up --build -d
   ```

2. **Check container status:**
   ```bash
   docker-compose ps
   ```

3. **(Optional) Run database setup script:**
   ```bash
   docker-compose exec backend python scripts/setup_db.py
   ```


## 6. Monitoring and Maintenance

1. **View logs**:
   ```bash
   docker-compose logs -f backend  # View backend logs
   docker-compose logs -f frontend # View frontend logs
   ```

2. **Set up automatic backups**:
   ```bash
   chmod +x backup.sh
   
   # Add to crontab
   (crontab -l 2>/dev/null; echo "0 2 * * * /home/$(whoami)/caspian/backup.sh") | crontab -
   ```

3. **Access Grafana dashboard**:
   - Navigate to `http://your-server-ip:3000`
   - Default login: admin/admin
   - Configure dashboards to monitor your system


## 7. CI/CD with GitHub Actions

1. **Generate SSH key for deployment**:
   ```bash
   ssh-keygen -t rsa -b 4096 -C "deployment-key" -f ./deployment-key
   ```

2. **Add public key to VM**:
   ```bash
   cat deployment-key.pub >> ~/.ssh/authorized_keys
   ```

3. **Add secrets to GitHub repository**:
   - Go to your GitHub repository → Settings → Secrets and Variables → Actions
   - Add the following secrets:
     - `GCP_PROJECT_ID`: Your GCP project ID
     - `GCP_SA_KEY`: Service account key with compute instance access
     - `VM_SSH_KEY`: Private key from deployment-key file
     - `VM_USER`: Your username on the VM
     - `DB_PASSWORD`: Database password
     - `SECRET_KEY`: Application secret key
     - `DISCORD_TOKEN`: Discord token
     - `GEMINI_API_KEY`: Gemini API key

4. **Push to GitHub to trigger deployment**:
   ```bash
   git add .
   git commit -m "Update application"
   git push
   ```


---

## Performance Tuning

### Docker Performance

1. **Increase Docker memory limits** (if needed):
   ```bash
   # Add to /etc/docker/daemon.json
   {
     "default-shm-size": "1G"
   }
   ```

2. **Restart Docker**:
   ```bash
   sudo systemctl restart docker
   ```

### PostgreSQL Tuning

1. **Add PostgreSQL configuration** to `docker-compose.yml`:
   ```yaml
   db:
     # ... existing config
     command: postgres -c shared_buffers=256MB -c work_mem=16MB
   ```

### Nginx Performance

1. **Optimize frontend Nginx**:
   - Update the `nginx.conf` with worker optimizations
   - Enable compression and caching


---

## Troubleshooting

1. **Container won't start**:
   ```bash
   docker-compose logs [service_name]
   ```

2. **Database connection issues**:
   ```bash
   docker-compose exec db psql -U caspian_user -d caspian_db -c "SELECT 1;"
   ```

3. **Reset and rebuild everything**:
   ```bash
   docker-compose down
   docker-compose up -d --force-recreate --build
   ```


---

## Backup and Restore

1. **Manual backup**:
   ```bash
   ./backup.sh
   ```

2. **Restore from backup**:
   ```bash
   # Stop the database
   docker-compose stop db
   
   # Start DB without dependencies
   docker-compose up -d db
   
   # Restore
   cat db-backups/backup_file.sql | docker-compose exec -T db psql -U caspian_user -d caspian_db
   
   # Restart everything
   docker-compose down
   docker-compose up -d
   ```


---

## Security Best Practices

1. **Keep system updated**:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

   ---

   ## Contact & Support

   - For issues, open a GitHub issue or discussion: https://github.com/ivinitus/caspian
   - For deployment help, see this guide and the main `README.md`.

   ---

2. **Set up UFW firewall**:
   ```bash
   sudo ufw allow ssh
   sudo ufw allow http
   sudo ufw allow https
   sudo ufw enable
   ```

3. **Secure PostgreSQL**:
   - Use strong passwords
   - Limit network access in docker-compose.yml

4. **Regular security audits**:
   - Scan for vulnerabilities with tools like Trivy
   - Update all packages and containers regularly
