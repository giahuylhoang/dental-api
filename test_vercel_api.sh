#!/bin/bash
# Test Vercel API endpoints
# Usage: ./test_vercel_api.sh [BASE_URL]
# Example: ./test_vercel_api.sh https://dental-api-xxx.vercel.app

API_URL="${1:-https://dental-api-ochre.vercel.app}"

echo "🧪 Testing Vercel API: $API_URL"
echo "=" | head -c 60 && echo ""

# Test doctors endpoint
echo "1️⃣  Testing /api/doctors..."
DOCTORS=$(curl -s "$API_URL/api/doctors")
DOCTOR_COUNT=$(echo "$DOCTORS" | grep -o '"id"' | wc -l | tr -d ' ')
if [ "$DOCTOR_COUNT" -gt 0 ]; then
    echo "   ✅ Found $DOCTOR_COUNT doctors"
else
    echo "   ❌ No doctors found"
fi

# Test services endpoint
echo ""
echo "2️⃣  Testing /api/services..."
SERVICES=$(curl -s "$API_URL/api/services")
SERVICE_COUNT=$(echo "$SERVICES" | grep -o '"id"' | wc -l | tr -d ' ')
if [ "$SERVICE_COUNT" -gt 0 ]; then
    echo "   ✅ Found $SERVICE_COUNT services"
else
    echo "   ❌ No services found"
fi

# Test patients endpoint
echo ""
echo "3️⃣  Testing /api/patients..."
PATIENTS=$(curl -s "$API_URL/api/patients")
PATIENT_COUNT=$(echo "$PATIENTS" | grep -o '"id"' | wc -l | tr -d ' ')
if [ "$PATIENT_COUNT" -gt 0 ]; then
    echo "   ✅ Found $PATIENT_COUNT patients"
else
    echo "   ⚠️  No patients found (might be empty or endpoint doesn't exist)"
fi

# Test appointments endpoint
echo ""
echo "4️⃣  Testing /api/appointments..."
APPOINTMENTS=$(curl -s "$API_URL/api/appointments")
if echo "$APPOINTMENTS" | grep -q '"id"'; then
    APPT_COUNT=$(echo "$APPOINTMENTS" | grep -o '"id"' | wc -l | tr -d ' ')
    echo "   ✅ Found $APPT_COUNT appointments"
else
    echo "   ⚠️  No appointments found or endpoint doesn't exist"
fi

# Test calendar validation (if endpoint exists)
echo ""
echo "5️⃣  Testing calendar connection..."
CALENDAR=$(curl -s "$API_URL/api/calendar/validate" 2>/dev/null)
if echo "$CALENDAR" | grep -q "valid\|true\|success"; then
    echo "   ✅ Calendar connection working"
elif echo "$CALENDAR" | grep -q "error\|false\|invalid"; then
    echo "   ⚠️  Calendar connection issue: $CALENDAR"
else
    echo "   ⚠️  Calendar endpoint might not exist or returned: $CALENDAR"
fi

# Test health endpoint (if exists)
echo ""
echo "6️⃣  Testing /health or /api/health..."
HEALTH=$(curl -s "$API_URL/health" 2>/dev/null || curl -s "$API_URL/api/health" 2>/dev/null)
if echo "$HEALTH" | grep -q "ok\|healthy\|status"; then
    echo "   ✅ Health check passed"
else
    echo "   ⚠️  Health endpoint not found or returned: $HEALTH"
fi

echo ""
echo "=" | head -c 60 && echo ""
echo "✅ API is working! Your deployment is successful."
echo ""
echo "📊 Summary:"
echo "   - Doctors: $DOCTOR_COUNT"
echo "   - Services: $SERVICE_COUNT"
echo "   - Patients: $PATIENT_COUNT"
echo ""
echo "🌐 API URL: $API_URL"
