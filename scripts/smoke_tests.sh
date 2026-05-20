#!/bin/bash
NEW_URL="https://dental-api-v2-832665048827.northamerica-northeast2.run.app"

echo "=== (a) Process health ==="
curl -s -o /dev/null -w "health: %{http_code}\n" "$NEW_URL/health"

echo "=== (b) DB connection sanity ==="
curl -s -H "X-Clinic-Id: default" "$NEW_URL/api/doctors" | head -c 100
echo

echo "=== (c) Per-clinic config (default) ==="
curl -s -H "X-Clinic-Id: default" "$NEW_URL/api/clinic" | head -c 100
echo

echo "=== (d) Second clinic (market-mall-denture) ==="
curl -s -H "X-Clinic-Id: market-mall-denture" "$NEW_URL/api/clinic" | head -c 100
echo

echo "=== (e) SSE liveness ==="
curl -s -N --max-time 10 "$NEW_URL/api/v2/events/stream?clinic_id=default" | head -10

echo "=== (f) End-to-end booking write ==="
curl -s -N --max-time 10 "$NEW_URL/api/v2/events/stream?clinic_id=default" > /tmp/sse_output &
SSE_PID=$!
sleep 2

curl -s -X POST -H "Content-Type: application/json" -H "X-Clinic-Id: default" \
  -d '{"patient_name":"Smoke Test","service_id":1,"provider_id":1,"start_time":"2026-06-01T15:00:00"}' \
  "$NEW_URL/api/calendar/events" | head -c 100
echo

sleep 2
echo "SSE Output:"
cat /tmp/sse_output

kill $SSE_PID || true

echo "=== (g) Logs sanity ==="
gcloud run services logs read dental-api-v2 \
  --region=northamerica-northeast2 \
  --limit=50 \
  | grep -iE "error|exception|traceback" | head -20
