# Your Vercel Deployment URLs

## Your URLs

1. **Production Domain:** `dental-api-ochre.vercel.app`
   - This is your main production URL
   - Use this for your agent's `CALENDAR_API_URL`
   - Always available

2. **Preview/Deployment URL:** `dental-c5u6ce3gb-gia-huy-hoangs-projects.vercel.app`
   - This is a preview URL for this specific deployment
   - Changes with each deployment
   - Good for testing specific deployments

## Use Production URL

For your agent configuration, use:
```
CALENDAR_API_URL=https://dental-api-ochre.vercel.app
```

## Quick Test

```bash
# Test health endpoint
curl https://dental-api-ochre.vercel.app/health

# Should return: {"status": "ok"}
```

## Next Steps

1. ✅ Test API is working
2. ✅ Initialize database
3. ✅ Verify endpoints
4. ✅ Update agent with production URL
