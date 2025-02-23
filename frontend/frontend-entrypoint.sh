#!/bin/sh
echo "⏳ Waiting for backend to load database with data from yahoo finance. This may take a while (especially on the first run)"

while true; do
    RESPONSE=$(curl -s http://backend:8000 | jq -r '.status' 2>/dev/null)  # Extract "status" field
    if [ "$RESPONSE" = "pass" ]; then
        echo "✅ Backend is ready!"
        break
    fi

    sleep 2
done

npm run dev
