#!/bin/bash

# Streaming "Passed" Use Case
# This demonstrates Server-Sent Events (SSE), the ScrapingAgent, and the Report Agent.

API_KEY="shared-secret-with-nestjs-backend"
IMAGE_URL="http://localhost:8888/diploma.png"

echo "Executing Streaming Pipeline..."
echo "--------------------------------"

curl -N -X POST "http://localhost:8000/api/pipeline" \
     -H "Content-Type: application/json" \
     -H "x-internal-api-key: $API_KEY" \
     -d "{
  \"documents\": [
    {
      \"file_url\": \"$IMAGE_URL\",
      \"doc_type_hint\": \"national_id\"
    },
    {
      \"file_url\": \"$IMAGE_URL\",
      \"doc_type_hint\": \"diplome_medecine\"
    },
    {
      \"file_url\": \"$IMAGE_URL\",
      \"doc_type_hint\": \"attestation_affiliation_cnas\"
    }
  ],
  \"kyc_result\": {\"passed\": true, \"liveness_score\": 0.95},
  \"trust_threshold\": 75.0,
  \"stream\": true
}"
