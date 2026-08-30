#!/bin/bash
# Switch the active gcloud project to GSF.
# Usage: ./set-gcloud-project.sh
#        source ./set-gcloud-project.sh   # also sets PROJECT_ID in the caller

PROJECT_ID="focused-mote-477703-f0"

echo "Setting gcloud project to $PROJECT_ID..."
gcloud config set project "$PROJECT_ID"
echo "Current project: $(gcloud config get-value project 2>/dev/null)"
