#!/bin/bash

# GCP Deployment Script for Sample OpenRouter Backend
# This script deploys the FastAPI application to Google Cloud Platform

set -e

# Configuration
PROJECT_ID="your-project-id"
REGION="us-central1"
SERVICE_NAME="sample-openrouter-backend"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
SERVICE_ACCOUNT="sample-openrouter-backend-sa@${PROJECT_ID}.iam.gserviceaccount.com"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting GCP deployment for Sample OpenRouter Backend${NC}"

# Check if required tools are installed
check_requirements() {
    echo -e "${YELLOW}Checking requirements...${NC}"
    
    if ! command -v gcloud &> /dev/null; then
        echo -e "${RED}❌ gcloud CLI is not installed. Please install it first.${NC}"
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker is not installed. Please install it first.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Requirements check passed${NC}"
}

# Authenticate with GCP
authenticate() {
    echo -e "${YELLOW}Authenticating with GCP...${NC}"
    
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        echo "Please authenticate with GCP:"
        gcloud auth login
    fi
    
    gcloud config set project $PROJECT_ID
    echo -e "${GREEN}✅ Authentication successful${NC}"
}

# Enable required APIs
enable_apis() {
    echo -e "${YELLOW}Enabling required GCP APIs...${NC}"
    
    gcloud services enable cloudbuild.googleapis.com
    gcloud services enable run.googleapis.com
    gcloud services enable containerregistry.googleapis.com
    
    echo -e "${GREEN}✅ APIs enabled${NC}"
}

# Create service account if it doesn't exist
create_service_account() {
    echo -e "${YELLOW}Setting up service account...${NC}"
    
    if ! gcloud iam service-accounts describe $SERVICE_ACCOUNT &> /dev/null; then
        echo "Creating service account..."
        gcloud iam service-accounts create sample-openrouter-backend-sa \
    --display-name="Sample OpenRouter Backend Service Account" \
    --description="Service account for Sample OpenRouter Backend"
        
        # Grant necessary permissions
        gcloud projects add-iam-policy-binding $PROJECT_ID \
            --member="serviceAccount:$SERVICE_ACCOUNT" \
            --role="roles/run.admin"
        
        gcloud projects add-iam-policy-binding $PROJECT_ID \
            --member="serviceAccount:$SERVICE_ACCOUNT" \
            --role="roles/storage.admin"
        
        gcloud projects add-iam-policy-binding $PROJECT_ID \
            --member="serviceAccount:$SERVICE_ACCOUNT" \
            --role="roles/iam.serviceAccountUser"
    else
        echo "Service account already exists"
    fi
    
    echo -e "${GREEN}✅ Service account ready${NC}"
}

# Build and push Docker image
build_and_push() {
    echo -e "${YELLOW}Building and pushing Docker image...${NC}"
    
    # Configure Docker to use gcloud as a credential helper
    gcloud auth configure-docker
    
    # Build the image
    docker build -t $IMAGE_NAME .
    
    # Push to Container Registry
    docker push $IMAGE_NAME
    
    echo -e "${GREEN}✅ Image built and pushed${NC}"
}

# Deploy to Cloud Run
deploy() {
    echo -e "${YELLOW}Deploying to Cloud Run...${NC}"
    
    gcloud run deploy $SERVICE_NAME \
        --image $IMAGE_NAME \
        --platform managed \
        --region $REGION \
        --service-account $SERVICE_ACCOUNT \
        --allow-unauthenticated \
        --memory 2Gi \
        --cpu 2 \
        --max-instances 10 \
        --timeout 300 \
        --concurrency 80 \
        --set-env-vars="LOG_LEVEL=INFO" \
        --set-env-vars="OPENROUTER_BASE_URL=https://openrouter.ai/api/v1" \
        --set-env-vars="RATE_LIMIT_REQUESTS=10" \
        --set-env-vars="RATE_LIMIT_WINDOW=60" \
        --set-env-vars="MAX_RETRIES=3" \
        --set-env-vars="REQUEST_TIMEOUT=30"
    
    echo -e "${GREEN}✅ Deployment successful${NC}"
}

# Get service URL
get_service_url() {
    echo -e "${YELLOW}Getting service URL...${NC}"
    
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)")
    
    echo -e "${GREEN}🌐 Service URL: ${SERVICE_URL}${NC}"
    echo -e "${GREEN}📚 API Documentation: ${SERVICE_URL}/docs${NC}"
}

# Main deployment flow
main() {
    check_requirements
    authenticate
    enable_apis
    create_service_account
    build_and_push
    deploy
    get_service_url
    
    echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Set environment variables in Cloud Run:"
    echo "   - OPENROUTER_API_KEY"
    echo "   - SECRET_KEY"
    echo "   - OPENROUTER_MODELS"
    echo "2. Test the service: curl ${SERVICE_URL}/health"
    echo "3. Generate access tokens using the token generation script"
}

# Run main function
main "$@"
