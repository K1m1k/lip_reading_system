#!/bin/bash

# Script per il deployment su cloud
ENVIRONMENT=$1

case $ENVIRONMENT in
  "aws")
    echo "Deploying to AWS..."
    aws ecs update-service --cluster lip_recognition_cluster --service lip_recognition_service --force-new-deployment
    ;;
  "azure")
    echo "Deploying to Azure..."
    az webapp restart --name lip-recognition-app --resource-group lip-recognition-rg
    ;;
  "gcp")
    echo "Deploying to GCP..."
    gcloud app deploy app.yaml --version=prod --project=lip-recognition-project
    ;;
  *)
    echo "Usage: $0 {aws|azure|gcp}"
    exit 1
    ;;
esac
