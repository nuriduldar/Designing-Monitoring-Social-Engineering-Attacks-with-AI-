#!/bin/bash

# Public erişim için Flask'ı başlatma scripti
# Kullanım: ./start_public.sh

set -e

echo "=========================================="
echo "Starting Social Engineering AI - Public Access"
echo "=========================================="

# IP adresini bul
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "localhost")
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    IP=$(hostname -I | awk '{print $1}')
else
    IP="localhost"
fi

echo ""
echo "🌐 Access URLs:"
echo "   Local:    http://localhost:5000"
echo "   Network:  http://${IP}:5000"
echo ""
echo "📋 To share with others on the same network:"
echo "   http://${IP}:5000"
echo ""
echo "🌍 For internet access, use ngrok:"
echo "   1. Install: brew install ngrok"
echo "   2. Run: ngrok http 5000"
echo "   3. Share the ngrok link"
echo ""
echo "⚠️  Remember: This is a TEST ENVIRONMENT"
echo ""
echo "Starting Flask server..."
echo "=========================================="
echo ""

cd "$(dirname "$0")"
python3 sim_server/app.py

