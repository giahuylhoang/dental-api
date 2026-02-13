#!/bin/bash
# Helper script to add GOOGLE_SERVICE_ACCOUNT_JSON to Vercel

echo "🔐 Adding GOOGLE_SERVICE_ACCOUNT_JSON to Vercel"
echo "=" | head -c 60 && echo ""

# Check if .env.local exists
if [ ! -f "dental-api/.env.local" ]; then
    echo "❌ Error: dental-api/.env.local not found"
    exit 1
fi

# Load the service account JSON from .env.local
source <(grep "^GOOGLE_SERVICE_ACCOUNT_JSON=" dental-api/.env.local | sed 's/^GOOGLE_SERVICE_ACCOUNT_JSON=//' | sed "s/^'//" | sed "s/'$//")

if [ -z "$GOOGLE_SERVICE_ACCOUNT_JSON" ]; then
    echo "❌ GOOGLE_SERVICE_ACCOUNT_JSON not found in .env.local"
    echo ""
    echo "💡 First add it locally:"
    echo "   python3 dental-api/add_service_account.py"
    exit 1
fi

echo "✅ Found GOOGLE_SERVICE_ACCOUNT_JSON in .env.local"
echo "   Length: ${#GOOGLE_SERVICE_ACCOUNT_JSON} characters"
echo ""

# Extract email for confirmation
EMAIL=$(echo "$GOOGLE_SERVICE_ACCOUNT_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin).get('client_email', 'NOT FOUND'))" 2>/dev/null)
if [ "$EMAIL" != "NOT FOUND" ]; then
    echo "   Service Account Email: $EMAIL"
    echo ""
fi

echo "📝 Adding to Vercel..."
echo ""
echo "⚠️  You'll be prompted to paste the JSON value."
echo "   The value will be shown below - you can copy it."
echo ""
echo "Press Enter to continue, or Ctrl+C to cancel..."
read

# Show the JSON (first 100 chars)
echo "JSON value (first 100 chars):"
echo "$GOOGLE_SERVICE_ACCOUNT_JSON" | head -c 100
echo "..."
echo ""

# Add to Vercel
echo "Adding to Vercel (Production)..."
echo "$GOOGLE_SERVICE_ACCOUNT_JSON" | vercel env add GOOGLE_SERVICE_ACCOUNT_JSON production

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Successfully added to Vercel Production!"
    echo ""
    echo "📝 Next steps:"
    echo "   1. Also add to Preview environment (optional but recommended):"
    echo "      echo '$GOOGLE_SERVICE_ACCOUNT_JSON' | vercel env add GOOGLE_SERVICE_ACCOUNT_JSON preview"
    echo ""
    echo "   2. Redeploy your application:"
    echo "      cd dental-api"
    echo "      vercel deploy --prod"
    echo ""
    echo "   3. Test the calendar endpoint:"
    echo "      curl https://dental-api-ochre.vercel.app/api/admin/calendar/validate"
    echo ""
else
    echo ""
    echo "❌ Failed to add to Vercel"
    echo ""
    echo "💡 Manual steps:"
    echo "   1. Go to: https://vercel.com/dashboard"
    echo "   2. Select project: dental-api-ochre"
    echo "   3. Settings → Environment Variables"
    echo "   4. Add: GOOGLE_SERVICE_ACCOUNT_JSON"
    echo "   5. Value: (paste the JSON below)"
    echo ""
    echo "$GOOGLE_SERVICE_ACCOUNT_JSON"
fi
