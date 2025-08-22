#!/bin/bash
# Caspian VM Setup Script

# Exit on error
set -e

# Configuration - Change these values
PROJECT_ID="caspian-project"
ZONE="us-central1-a"
VM_NAME="caspian-server"
MACHINE_TYPE="e2-standard-2"  # 2vCPU, 8GB RAM
DISK_SIZE="30GB"
DB_PASSWORD="CHANGE_THIS_TO_SECURE_PASSWORD"
SECRET_KEY="CHANGE_THIS_TO_SECURE_KEY"
DISCORD_TOKEN="YOUR_DISCORD_TOKEN"
GEMINI_API_KEY="YOUR_GEMINI_API_KEY"

echo "===== Step 1: Set up GCP Project ====="
# Set the project
gcloud config set project $PROJECT_ID

# Enable APIs
echo "Enabling required GCP services..."
gcloud services enable compute.googleapis.com

echo "===== Step 2: Create VM Instance ====="
echo "Creating VM instance (this may take a few minutes)..."
gcloud compute instances create $VM_NAME \
  --zone=$ZONE \
  --machine-type=$MACHINE_TYPE \
  --boot-disk-size=$DISK_SIZE \
  --image-family=ubuntu-2004-lts \
  --image-project=ubuntu-os-cloud \
  --tags=http-server,https-server

echo "Opening firewall ports..."
gcloud compute firewall-rules create allow-http \
  --allow tcp:80 \
  --target-tags http-server

gcloud compute firewall-rules create allow-https \
  --allow tcp:443 \
  --target-tags https-server

echo "===== Step 3: Prepare Setup Script ====="
# Create a setup script to run on the VM
cat > setup.sh << 'EOF'
#!/bin/bash
set -e

# Install Docker and Docker Compose
echo "Installing Docker and Docker Compose..."
sudo apt update
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io git
sudo usermod -aG docker ${USER}

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Clone repository
echo "Cloning repository..."
git clone https://github.com/yourusername/caspian.git
cd caspian

# Create .env file
echo "Creating environment file..."
cat > .env << 'ENVEOF'
DB_PASSWORD=DB_PASSWORD_PLACEHOLDER
SECRET_KEY=SECRET_KEY_PLACEHOLDER
DISCORD_TOKEN=DISCORD_TOKEN_PLACEHOLDER
GEMINI_API_KEY=GEMINI_API_KEY_PLACEHOLDER
ENVEOF

# Create docker-compose.yml file
echo "Creating docker-compose.yml..."
cat > docker-compose.yml << 'COMPOSEEOF'
version: '3.8'
services:
  backend:
    build: ./caspian/backend
    restart: always
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://caspian_user:${DB_PASSWORD}@db:5432/caspian_db
      - DISCORD_TOKEN=${DISCORD_TOKEN}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - db
  
  frontend:
    build: ./caspian/frontend/web
    restart: always
    ports:
      - "80:80"
    environment:
      - VITE_API_URL=http://localhost:8000
    depends_on:
      - backend
  
  db:
    image: pgvector/pgvector:pg15
    restart: always
    environment:
      POSTGRES_USER: caspian_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: caspian_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
COMPOSEEOF

echo "Setup completed! Log out and log back in for Docker permissions to take effect."
echo "Then run: cd caspian && docker-compose up -d"
EOF

# Replace placeholders in the setup script
sed -i "s/DB_PASSWORD_PLACEHOLDER/$DB_PASSWORD/g" setup.sh
sed -i "s/SECRET_KEY_PLACEHOLDER/$SECRET_KEY/g" setup.sh
sed -i "s/DISCORD_TOKEN_PLACEHOLDER/$DISCORD_TOKEN/g" setup.sh
sed -i "s/GEMINI_API_KEY_PLACEHOLDER/$GEMINI_API_KEY/g" setup.sh
sed -i "s/yourusername/ivinitus/g" setup.sh

echo "===== Step 4: Upload Setup Script to VM ====="
gcloud compute scp setup.sh $VM_NAME:~/setup.sh --zone=$ZONE

echo "===== Step 5: Run Setup Script on VM ====="
gcloud compute ssh $VM_NAME --zone=$ZONE --command="chmod +x setup.sh && ./setup.sh"

echo "===== Setup Complete ====="
echo "VM has been created and initial setup is complete."
echo "To finish deployment:"
echo "1. SSH into your VM: gcloud compute ssh $VM_NAME --zone=$ZONE"
echo "2. Log out and log back in for Docker permissions to take effect"
echo "3. Deploy the application: cd caspian && docker-compose up -d"
echo ""
echo "Your VM's external IP is:"
gcloud compute instances describe $VM_NAME --zone=$ZONE --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
