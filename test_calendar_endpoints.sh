#!/bin/bash
# Test calendar-related API endpoints

API_URL="https://dental-api-ochre.vercel.app"

echo "🧪 Testing Calendar API Endpoints"
echo "=" | head -c 60 && echo ""

# Test calendar validation
echo "1️⃣  Testing /api/admin/calendar/validate..."
VALIDATE=$(curl -s "$API_URL/api/admin/calendar/validate")
if echo "$VALIDATE" | grep -q '"status":"valid"'; then
    echo "   ✅ Calendar credentials are valid!"
    echo "$VALIDATE" | python3 -m json.tool 2>/dev/null || echo "$VALIDATE"
elif echo "$VALIDATE" | grep -q '"status":"invalid"'; then
    echo "   ❌ Calendar credentials invalid"
    echo "$VALIDATE" | python3 -m json.tool 2>/dev/null || echo "$VALIDATE"
else
    echo "   ⚠️  Unexpected response:"
    echo "$VALIDATE" | python3 -m json.tool 2>/dev/null || echo "$VALIDATE"
fi

# Test calendar slots (requires date parameters)
echo ""
echo "2️⃣  Testing /api/calendar/slots..."
# Get tomorrow's date
TOMORROW=$(date -v+1d +%Y-%m-%d 2>/dev/null || date -d "+1 day" +%Y-%m-%d)
START_TIME="${TOMORROW}T09:00:00"
END_TIME="${TOMORROW}T17:00:00"

SLOTS=$(curl -s "$API_URL/api/calendar/slots?start_datetime=${START_TIME}&end_datetime=${END_TIME}")
if echo "$SLOTS" | grep -q '"slots"'; then
    SLOT_COUNT=$(echo "$SLOTS" | grep -o '"start"' | wc -l | tr -d ' ')
    echo "   ✅ Found $SLOT_COUNT available slots"
    echo "   (Showing first 3 slots)"
    echo "$SLOTS" | python3 -c "import sys, json; data=json.load(sys.stdin); print(json.dumps({'slots': data.get('slots', [])[:3]}, indent=2))" 2>/dev/null || echo "$SLOTS" | head -20
else
    echo "   ⚠️  Response:"
    echo "$SLOTS" | python3 -m json.tool 2>/dev/null || echo "$SLOTS"
fi

echo ""
echo "=" | head -c 60 && echo ""
echo "📋 Available Calendar Endpoints:"
echo "   GET  /api/admin/calendar/validate - Validate credentials"
echo "   POST /api/admin/calendar/refresh - Refresh token"
echo "   GET  /api/calendar/slots - Get available slots"
echo "   POST /api/calendar/events - Create calendar event"
echo ""
echo "🌐 API URL: $API_URL"
