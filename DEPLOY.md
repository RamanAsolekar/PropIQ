# PropIQ Deployment Guide
## Get a live URL in under 10 minutes (free)

---

## Option A — Railway (Recommended, Fastest)

Railway gives you a live HTTPS URL for free.

```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login
railway login

# 3. From propiq/ root:
railway init
railway up

# Railway auto-detects railway.json
# Your URL: https://propiq-backend-xxxx.railway.app
```

Then deploy the frontend to Vercel:
```bash
cd frontend
npm install -g vercel
vercel --env REACT_APP_API_URL=https://your-railway-url.railway.app
```

---

## Option B — Render.com (Zero config)

1. Push your code to GitHub
2. Go to render.com → New → Blueprint
3. Connect your repo — Render reads `render.yaml` automatically
4. Both backend and frontend deploy in one click

---

## Option C — Local network demo (simplest for video)

```bash
# Backend
cd propiq/backend
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Frontend
cd propiq/frontend
REACT_APP_API_URL=http://localhost:8000 npm start
```

---

## Environment Variables

| Variable | Required | Value |
|----------|----------|-------|
| `ANTHROPIC_API_KEY` | Optional | For live LLM narration. Without it, uses deterministic fallback. |
| `DEBUG` | No | `false` in production |
| `REACT_APP_API_URL` | Yes (prod) | Your backend URL |

---

## Verifying the deployment

```bash
# Health check
curl https://your-url/api/v1/health

# Quick assessment
curl -X POST https://your-url/api/v1/assess \
  -H "Content-Type: application/json" \
  -H "X-API-Key: propiq-demo-2026" \
  -d '{"locality":"Baner","prop_type":"2bhk_apartment","size_sqft":850,"age_years":8}'
```

---

## For the Hackathon Submission

Include in your GitHub README:
- Live backend URL: `https://your-backend.railway.app/docs`
- Live frontend URL: `https://your-frontend.vercel.app`
- Demo video: Screen recording following DEMO_SCRIPT.md
- Test API key: `propiq-demo-2026`