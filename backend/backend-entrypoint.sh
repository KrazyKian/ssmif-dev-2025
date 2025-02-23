#!/bin/sh
TOKEN_FILE="/shared/influx_token.txt"
#!/bin/sh
echo "⏳ Waiting for InfluxDB to be ready..."

# Retry until InfluxDB responds
MAX_RETRIES=30  # 30 retries (60 seconds)
RETRY_COUNT=0


while true; do
    RESPONSE=$(curl -s http://influxdb:8086/health | jq -r '.status' 2>/dev/null)  # Extract "status" field
    if [ "$RESPONSE" = "pass" ]; then
        echo "✅ InfluxDB is ready!"
        break
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "❌ InfluxDB did not start in time. Exiting."
        exit 1
    fi

    echo "⏳ Still waiting for InfluxDB... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done


echo "⏳ Checking if InfluxDB is already set up..."

SETUP_CHECK=$(curl -s http://influxdb:8086/api/v2/setup )
echo "SETUP_CHECK: $SETUP_CHECK"
SETUP_CHECK=$(echo "$SETUP_CHECK" | jq -r '.allowed')

if [ "$SETUP_CHECK" = "true" ]; then
    echo "🚀 InfluxDB is not set up yet. Proceeding with setup..."
    
    SETUP_RESPONSE=$(curl -s -X POST http://influxdb:8086/api/v2/setup \
      --header "Content-Type: application/json" \
      --data "{
        \"org\": \"$INFLUXDB_ORG\",
        \"bucket\": \"$INFLUXDB_BUCKET\",
        \"username\": \"$INFLUXDB_USERNAME\",
        \"password\": \"$INFLUXDB_PASSWORD\",
        \"retentionPeriodSeconds\": 0
      }")

    ADMIN_TOKEN=$(echo "$SETUP_RESPONSE" | jq -r '.auth.token')

    if [ -z "$ADMIN_TOKEN" ] || [ "$ADMIN_TOKEN" = "null" ]; then
        echo "❌ ERROR: Failed to set up InfluxDB. Exiting..."
        exit 1
    fi

    echo "✅ InfluxDB setup complete. Storing token in shared volume."

    # Store the token in the shared volume
    echo "$ADMIN_TOKEN" > "$TOKEN_FILE"
else
    echo "✅ InfluxDB is already set up."

    # Read the stored token from shared volume
    if [ -f "$TOKEN_FILE" ]; then
        ADMIN_TOKEN=$(cat "$TOKEN_FILE")
        echo "✅ Retrieved stored token from shared volume."
    else
        echo "❌ ERROR: No stored token found. Ensure InfluxDB setup completed correctly."
        exit 1
    fi
fi

export INFLUXDB_TOKEN="$ADMIN_TOKEN"
echo "✅ Using INFLUX_TOKEN: $INFLUXDB_TOKEN"

# Start the FastAPI backend
echo "🚀 Starting FastAPI backend..."
exec uvicorn mains:app --host 0.0.0.0 --port 8000 --log-level debug
