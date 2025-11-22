# 🚀 Complete Deployment Guide - DocaCast with Full Features

This guide will help you deploy DocaCast with **ALL features working perfectly**. We'll use a hybrid approach:
- **Vercel** → Frontend (React app)
- **Render/Railway** → Backend (FastAPI with full processing)

---

## 🎯 Deployment Strategy Overview

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│  User Browser → Vercel (Frontend)                   │
│                    ↓                                │
│              API Calls                              │
│                    ↓                                │
│         Render/Railway (Backend)                    │
│    ✓ PDF Processing                                │
│    ✓ Audio Generation                              │
│    ✓ Vector Search                                 │
│    ✓ FFmpeg Processing                             │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 📋 Prerequisites (5 minutes)

### Get Your API Keys:

1. **Google Gemini API Key** 🔑
   - Visit: https://makersuite.google.com/app/apikey
   - Click "Create API Key"
   - Copy and save it

2. **Adobe PDF Embed Client ID** 🔑
   - Visit: https://developer.adobe.com/console
   - Create new project
   - Add "PDF Embed API"
   - Copy the Client ID

---

## 🚀 Option A: Render (Recommended - Easiest)

### Why Render?
- ✅ Free tier available
- ✅ Auto-detects Python + requirements
- ✅ Built-in FFmpeg support
- ✅ Persistent storage (75GB free)
- ✅ Easy setup via web interface
- ✅ Automatic HTTPS

### Step 1: Deploy Backend on Render (10 minutes)

1. **Go to Render Dashboard**
   - Visit: https://dashboard.render.com
   - Sign up/Sign in (GitHub recommended)

2. **Create New Web Service**
   - Click: "New +" → "Web Service"
   - Connect your GitHub repository
   - Select "docacast" repo

3. **Configure Service**
   ```
   Name: docacast-backend
   Environment: Python 3
   Region: Choose closest to you
   Branch: main
   
   Root Directory: (leave blank)
   
   Build Command:
   pip install -r backend/requirements.txt
   
   Start Command:
   cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
   
   Plan: Free
   ```

4. **Add Environment Variables**
   Click "Advanced" → "Add Environment Variable":
   
   ```
   GOOGLE_API_KEY = [your Google API key]
   GEMINI_API_KEY = [same as GOOGLE_API_KEY]
   TTS_PROVIDER = gemini
   GEMINI_VOICE_A = Charon
   GEMINI_VOICE_B = Aoede
   PYTHON_VERSION = 3.11.0
   ```

5. **Create Service**
   - Click "Create Web Service"
   - Wait 5-10 minutes for deployment
   - Copy your backend URL (e.g., `https://docacast-backend.onrender.com`)

### Step 2: Deploy Frontend on Vercel (5 minutes)

1. **Update Frontend Environment**
   - Go to your local project
   - Open `frontend/pdf-reader-ui/.env` (create if doesn't exist)
   - Add:
   ```env
   VITE_API_BASE_URL=https://docacast-backend.onrender.com
   VITE_ADOBE_CLIENT_ID=your_adobe_client_id
   ```

2. **Commit and Push**
   ```bash
   git add .
   git commit -m "Configure for Render backend deployment"
   git push origin main
   ```

3. **Deploy on Vercel**
   - Go to: https://vercel.com/dashboard
   - Click "Add New..." → "Project"
   - Import your repository
   - Framework: **Vite** (auto-detected)
   - Root Directory: `./`
   - Build Command: `cd frontend/pdf-reader-ui && npm install && npm run build`
   - Output Directory: `frontend/pdf-reader-ui/dist`

4. **Add Environment Variables in Vercel**
   ```
   VITE_API_BASE_URL = https://docacast-backend.onrender.com
   VITE_ADOBE_CLIENT_ID = [your Adobe client ID]
   ```

5. **Deploy**
   - Click "Deploy"
   - Wait 2-3 minutes
   - Your app is live! 🎉

---

## 🚂 Option B: Railway (More Features)

### Why Railway?
- ✅ Better performance than Render free tier
- ✅ More generous resources
- ✅ Automatic domain + HTTPS
- ✅ GitHub integration
- ✅ $5/month starter plan (5GB RAM, 50GB storage)

### Step 1: Deploy Backend on Railway (10 minutes)

1. **Go to Railway**
   - Visit: https://railway.app
   - Sign up with GitHub

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your DocaCast repository

3. **Configure Service**
   - Railway auto-detects Python
   - It will use the `railway.json` configuration I created
   
4. **Add Environment Variables**
   Go to your service → Variables tab:
   ```
   GOOGLE_API_KEY = [your Google API key]
   GEMINI_API_KEY = [same as GOOGLE_API_KEY]
   TTS_PROVIDER = gemini
   GEMINI_VOICE_A = Charon
   GEMINI_VOICE_B = Aoede
   ```

5. **Deploy**
   - Railway automatically deploys
   - Wait 5-8 minutes
   - Copy your backend URL from Settings → Domains

### Step 2: Deploy Frontend (Same as Render Option)

Follow "Step 2: Deploy Frontend on Vercel" from Option A above, using your Railway backend URL.

---

## 🐳 Option C: Docker (Any Platform)

If you prefer Docker, I've created a `Dockerfile` for you.

### Deploy on:
- **Render** (Docker)
- **Railway** (Docker)
- **Google Cloud Run**
- **AWS ECS**
- **DigitalOcean App Platform**

### Quick Docker Commands:

```bash
# Build
docker build -t docacast-backend .

# Run locally
docker run -p 8001:8001 \
  -e GOOGLE_API_KEY=your_key \
  docacast-backend

# Push to registry (for cloud deployment)
docker tag docacast-backend your-registry/docacast-backend
docker push your-registry/docacast-backend
```

---

## 🧪 Testing Your Deployment

### 1. Test Backend API

Visit: `https://your-backend-url.onrender.com/v1/health`

Expected response:
```json
{
  "status": "ok"
}
```

### 2. Test Frontend

Visit your Vercel URL: `https://your-app.vercel.app`

**Test Workflow:**
1. Upload a small PDF (2-3 pages)
2. View PDF in viewer
3. Click "Generate Podcast"
4. Wait for processing
5. Listen to the generated audio

### 3. Check Logs

**Render:**
- Go to your service → Logs tab
- Check for errors

**Railway:**
- Go to your service → Deployments → View Logs

**Vercel:**
- Go to project → Deployments → View Function Logs

---

## 🔧 Configuration Files Created

I've created these files for you:

1. **`render.yaml`** - Render configuration
2. **`railway.json`** - Railway configuration  
3. **`Dockerfile`** - Docker containerization
4. **`vercel.json`** (updated) - Frontend-only Vercel config

---

## 🎯 Recommended Setup (Best Performance)

**For Production:**
```
Frontend: Vercel (free)
Backend: Railway ($5/month)
Total Cost: $5/month
```

**For Free Tier:**
```
Frontend: Vercel (free)
Backend: Render (free)
Total Cost: $0/month
Note: Render free tier sleeps after inactivity (30 min cold start)
```

---

## 🆘 Troubleshooting

### Backend Won't Start

**Check:**
1. All environment variables are set
2. `backend/requirements.txt` is complete
3. Python version is 3.9-3.11
4. Check deployment logs for errors

**Common Issues:**
- Missing `GOOGLE_API_KEY` → Add in environment variables
- Module not found → Check requirements.txt
- Port binding error → Use `$PORT` variable

### Frontend Can't Reach Backend

**Check:**
1. `VITE_API_BASE_URL` is set correctly in Vercel
2. Backend URL is accessible (test /v1/health endpoint)
3. CORS is enabled (already configured in backend)
4. No trailing slash in API URL

**Fix:**
```bash
# Redeploy frontend with correct backend URL
vercel env add VITE_API_BASE_URL production
# Enter your backend URL when prompted
vercel --prod
```

### Audio Generation Fails

**Check:**
1. `GOOGLE_API_KEY` has Gemini API enabled
2. TTS_PROVIDER is set to 'gemini'
3. API quota isn't exceeded
4. Check backend logs for specific errors

### PDF Upload Fails

**Check:**
1. File size under 10MB
2. PDF is not corrupted
3. Backend has write permissions
4. Check backend storage space

---

## 📊 Performance Optimization

### For Render Free Tier:

**Issue:** Service sleeps after 15 minutes of inactivity

**Solution:** Use a keep-alive service (optional)
```bash
# Add to your frontend (ping every 14 minutes)
setInterval(() => {
  fetch('https://your-backend.onrender.com/v1/health')
}, 14 * 60 * 1000)
```

### For Better Performance:

1. **Upgrade to paid tier** ($7-25/month)
   - No sleep
   - More CPU/RAM
   - Faster processing

2. **Add CDN** for static files
   - Already handled by Vercel for frontend

3. **Enable caching** in backend
   - Already implemented in the code

---

## 🔒 Security Checklist

- [ ] API keys stored as environment variables (not in code)
- [ ] HTTPS enabled (automatic on Vercel/Render/Railway)
- [ ] CORS configured properly
- [ ] `.env` files in `.gitignore`
- [ ] Regular dependency updates
- [ ] Monitor API usage/costs

---

## 📈 Monitoring & Maintenance

### Render:
- Dashboard → Metrics (CPU, Memory, Requests)
- Set up email alerts for downtime

### Railway:
- Dashboard → Metrics
- Usage tracking
- Cost monitoring

### Vercel:
- Analytics (visitors, performance)
- Function logs
- Error tracking

---

## 🎉 Success Checklist

After deployment, verify:

- [ ] Backend health endpoint responds
- [ ] Frontend loads without errors
- [ ] PDF upload works
- [ ] Adobe PDF viewer displays documents
- [ ] Audio generation works (single speaker)
- [ ] Podcast generation works (two speakers)
- [ ] Semantic search works
- [ ] No CORS errors in browser console
- [ ] Environment variables are set
- [ ] Logs show no errors

---

## 💰 Cost Summary

### Free Option:
```
Vercel (Frontend): Free
Render (Backend): Free
Total: $0/month

Limitations:
- Backend sleeps after 15 min
- 750 hours/month compute
- Limited RAM/CPU
```

### Recommended Paid:
```
Vercel (Frontend): Free
Railway (Backend): $5/month
Total: $5/month

Benefits:
- No sleep
- 5GB RAM
- Better performance
- 50GB storage
```

---

## 🚀 Ready to Deploy?

### Quick Start Commands:

```bash
# 1. Commit your code
git add .
git commit -m "Add deployment configurations"
git push origin main

# 2. Deploy Backend (choose one):
# - Render: https://dashboard.render.com
# - Railway: https://railway.app

# 3. Deploy Frontend:
# - Vercel: https://vercel.com/dashboard
```

---

## 📞 Need Help?

- **Render Docs**: https://render.com/docs
- **Railway Docs**: https://docs.railway.app
- **Vercel Docs**: https://vercel.com/docs
- **Create Issue**: https://github.com/ironsupr/DocaCast/issues

---

**You're all set! Choose your deployment option and follow the steps above. All your DocaCast features will work perfectly! 🎙️✨**
