#!/bin/bash

# Test All AI Verification Service Endpoints
# This script hits every individual agent endpoint to demonstrate their isolated capabilities,
# and finishes by running the full pipeline.

API_KEY="shared-secret-with-nestjs-backend"
IMAGE_URL="http://localhost:8888/diploma.png"
BASE_URL="http://localhost:8000/api"

echo "=========================================="
echo "🧪 TESTING ALL AI VERIFICATION ENDPOINTS"
echo "=========================================="

# 1. Test Classifier
echo -e "\n\n1️⃣ Testing Classifier Agent (/api/classify)..."
curl -s -X POST "$BASE_URL/classify" \
     -H "Content-Type: application/json" \
     -H "x-internal-api-key: $API_KEY" \
     -d "{
  \"image_url\": \"$IMAGE_URL\"
}" | jq .

# 2. Test Extractor
echo -e "\n\n2️⃣ Testing Extraction Agent (/api/extract)..."
curl -s -X POST "$BASE_URL/extract" \
     -H "Content-Type: application/json" \
     -H "x-internal-api-key: $API_KEY" \
     -d "{
  \"image_url\": \"$IMAGE_URL\",
  \"doc_type\": \"diplome_medecine\",
  \"fields\": [
    {\"field_name\": \"first_name\", \"field_type\": \"text\"},
    {\"field_name\": \"last_name\", \"field_type\": \"text\"}
  ]
}" | jq .

# 3. Test Authenticity
echo -e "\n\n3️⃣ Testing Authenticity Agent (/api/authenticity)..."
curl -s -X POST "$BASE_URL/authenticity" \
     -H "Content-Type: application/json" \
     -H "x-internal-api-key: $API_KEY" \
     -d "{
  \"file_url\": \"$IMAGE_URL\",
  \"doc_type\": \"diplome_medecine\"
}" | jq .

# 4. Test Consistency
echo -e "\n\n4️⃣ Testing Consistency Agent (/api/consistency)..."
curl -s -X POST "$BASE_URL/consistency" \
     -H "Content-Type: application/json" \
     -H "x-internal-api-key: $API_KEY" \
     -d "{
  \"documents\": {
    \"diplome_medecine\": {
      \"first_name\": \"Ahmed\",
      \"last_name\": \"Benali\"
    },
    \"national_id\": {
      \"first_name\": \"Ahmed\",
      \"last_name\": \"Ben Ali\"
    }
  }
}" | jq .

# 5. Test Scoring
echo -e "\n\n5️⃣ Testing Scoring Agent (/api/score)..."
curl -s -X POST "$BASE_URL/score" \
     -H "Content-Type: application/json" \
     -H "x-internal-api-key: $API_KEY" \
     -d "{
  \"documents_submitted\": [\"national_id\", \"diplome_medecine\"],
  \"required_docs\": [\"national_id\"],
  \"authenticity_results\": {
    \"authenticity_score\": 95.0,
    \"is_suspicious\": false
  },
  \"consistency_result\": {
    \"overall_consistent\": true,
    \"consistency_score\": 100.0
  },
  \"trust_threshold\": 80.0
}" | jq .

# 6. Test Full Pipeline (No streaming)
echo -e "\n\n6️⃣ Testing Full Pipeline Orchestrator (/api/pipeline)..."
curl -s -X POST "$BASE_URL/pipeline" \
     -H "Content-Type: application/json" \
     -H "x-internal-api-key: $API_KEY" \
     -d "{
  \"documents\": [
    {
      \"file_url\": \"$IMAGE_URL\",
      \"doc_type_hint\": \"diplome_medecine\"
    }
  ],
  \"trust_threshold\": 75.0,
  \"stream\": false
}" | jq .

echo -e "\n\n✅ ALL TESTS COMPLETED!"
