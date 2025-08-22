#!/bin/bash
# Quick GCP Deployment Script for Caspian

# Exit on error
set -e

# Configuration
PROJECT_ID="caspian-project"  # Change this to your project ID
CLUSTER_NAME="caspian-cluster"
REGION="us-central1-a"

echo "===== Step 1: Set up GCP Project ====="
# Create project (uncomment if needed)
# gcloud projects create $PROJECT_ID --name="Caspian AI Assistant"
gcloud config set project $PROJECT_ID

# Enable APIs
echo "Enabling required GCP services..."
gcloud services enable container.googleapis.com \
    cloudbuild.googleapis.com \
    containerregistry.googleapis.com \
    compute.googleapis.com

echo "===== Step 2: Create Kubernetes Cluster ====="
# Create GKE cluster
echo "Creating Kubernetes cluster (this may take a few minutes)..."
gcloud container clusters create $CLUSTER_NAME \
    --zone $REGION \
    --num-nodes=3 \
    --machine-type=e2-standard-2

# Get credentials
echo "Getting cluster credentials..."
gcloud container clusters get-credentials $CLUSTER_NAME --zone $REGION

echo "===== Step 3: Deploy Caspian ====="
# Apply Kubernetes manifests
echo "Deploying Kubernetes resources..."
kubectl apply -f caspian/infra/k8s/secrets.yaml
kubectl apply -f caspian/infra/k8s/database-statefulset.yaml
kubectl apply -f caspian/infra/k8s/backend-deployment.yaml
kubectl apply -f caspian/infra/k8s/frontend-deployment.yaml

# Install NGINX Ingress
echo "Installing NGINX Ingress Controller..."
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml

# Wait for ingress controller to be ready
echo "Waiting for NGINX Ingress Controller to be ready..."
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=120s

# Install cert-manager
echo "Installing cert-manager for SSL..."
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.12.0/cert-manager.yaml

# Wait for cert-manager to be ready
echo "Waiting for cert-manager to be ready..."
kubectl wait --for=condition=ready pod -l app=cert-manager --timeout=60s -n cert-manager

# Apply certificate and ingress
echo "Deploying certificate and ingress..."
kubectl apply -f caspian/infra/k8s/certificate.yaml
kubectl apply -f caspian/infra/k8s/ingress.yaml

echo "===== Step 4: Get Access Information ====="
# Get ingress IP
echo "Waiting for ingress to get an external IP..."
sleep 60  # Give time for the ingress to get an external IP

INGRESS_IP=$(kubectl get service -n ingress-nginx ingress-nginx-controller -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

echo "===== Deployment Complete ====="
echo "Your Caspian application is deployed!"
echo "Frontend will be available at: https://caspian.app (point this domain to $INGRESS_IP)"
echo "API will be available at: https://api.caspian.app (point this domain to $INGRESS_IP)"
echo ""
echo "Run the following commands to check status:"
echo "  kubectl get pods            # Check if all pods are running"
echo "  kubectl get services        # View all services"
echo "  kubectl get ingress         # Check ingress status"
echo ""
echo "To view logs:"
echo "  kubectl logs -l app=backend   # Backend logs"
echo "  kubectl logs -l app=frontend  # Frontend logs"
