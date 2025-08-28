# Deploying Caspian on Your Own VM Instance

This is the official deployment guide for the Caspian AI Assistant platform using a VM instance on Google Cloud Platform (or any other cloud provider).

## Why Use a VM Instead of Other Deployment Methods?

A VM-based deployment offers several key advantages for the Caspian application:

1. **Consistent Performance**: No cold starts that can affect AI/ML workloads
2. **Cost Control**: Predictable pricing for consistent workloads
3. **Full Control**: Complete customization of your environment
4. **Simplified Architecture**: All components running together
5. **Better for AI Processing**: Dedicated resources for vector embeddings and AI operations

## Step 1: Create and Configure VM Instance

1. **Create a VM in Google Cloud**:
   ```bash
   gcloud compute instances create caspian-server \
     --zone=us-central1-a \
     --machine-type=e2-standard-4 \
     --boot-disk-size=50GB \
     --image-family=ubuntu-2004-lts \
     --image-project=ubuntu-os-cloud \
     --tags=http-server,https-server
   ```

2. **Open firewall ports**:
   ```bash
   gcloud compute firewall-rules create allow-http \
     --allow tcp:80 \
     --target-tags http-server
   
   gcloud compute firewall-rules create allow-https \
     --allow tcp:443 \
     --target-tags https-server
   ```

3. **SSH into your VM**:
   ```bash
   gcloud compute ssh caspian-server --zone=us-central1-a
   ```

## Step 2: Install Docker and Docker Compose

1. **Update packages and install dependencies**:
   ```bash
   sudo apt update
   sudo apt install -y apt-transport-https ca-certificates curl software-properties-common
   ```

2. **Install Docker**:
   ```bash
   # Add Docker's official GPG key using the new keyring method
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up the Docker repository
echo \
  "deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Update package index and install Docker CE
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add your user to the docker group for non-root access
sudo usermod -aG docker $USER

   ```

3. **Install Docker Compose**:
   ```bash
   sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

4. **Log out and log back in for group changes to take effect**:
   ```bash
   exit
   gcloud compute ssh caspian-server --zone=us-central1-a
   ```

## Step 3: Set Up Your Project

1. **Clone your repository**:
   ```bash
   git clone https://github.com/ivinitus/caspian.git
   cd caspian
   ```

2. **Create needed directories**:
   ```bash
   mkdir -p ssl nginx-logs db-backups
   ```

3. **Create a .env file for secrets**:
   ```bash
   touch .env
   nano .env
   ```

   Add the following content (replace with your actual values):
   ```
   DB_PASSWORD=your_secure_password
   SECRET_KEY=your_secure_key
   DISCORD_TOKEN=your_discord_token
   GEMINI_API_KEY=your_gemini_api_key
   ```

## Step 4: Configure SSL/TLS with Certbot

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

## Step 5: Deploy the Application

1. **Start the containers**:
   ```bash
   docker-compose up -d
   ```

2. **Check container status**:
   ```bash
   docker-compose ps
   ```

3. **Initialize database (first time only)**:
   ```bash
   docker-compose exec backend python -m app.scripts.setup_db
   ```

## Step 6: Monitoring and Maintenance

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

## Step 7: CI/CD with GitHub Actions

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

## Security Best Practices

1. **Keep system updated**:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

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
