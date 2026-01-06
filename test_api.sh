#!/bin/bash
echo "Testing API endpoints..."
echo ""
echo "1. Testing /api/generate/models..."
curl -s http://localhost:5000/api/generate/models | python3 -m json.tool || echo "❌ Failed"
echo ""
echo "2. Testing /api/model/status..."
curl -s http://localhost:5000/api/model/status | python3 -m json.tool || echo "❌ Failed"
echo ""
echo "3. Testing /api/generate (POST)..."
curl -s -X POST http://localhost:5000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"tone":"polite","role":"employee","use_openai":false,"use_llama":false,"use_gemini":false,"count":1}' | python3 -m json.tool || echo "❌ Failed"
