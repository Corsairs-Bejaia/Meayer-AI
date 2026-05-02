#!/bin/bash
set -e

echo "🧪 Running AI Service Tests..."
cd ai-service
uv run pytest tests/ -q
cd ..

echo -e "\n🧪 Running Scraping Service Tests..."
cd scraping-service
uv run pytest tests/ -q
cd ..

echo -e "\n✨ All tests passed!"
