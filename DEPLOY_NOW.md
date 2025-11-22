# ⚡ DEPLOY NOW - 20 Minutes to Live App

The fastest path to get DocaCast running with ALL features working.

---

## 🎯 What You're Deploying

✅ **Frontend** → Vercel (React/Vite)  
✅ **Backend** → Render (Python/FastAPI)  
✅ **Cost** → FREE  
✅ **Time** → 20 minutes  

**All Features Will Work:**
- PDF upload & processing
- AI-powered podcast generation
- Two-speaker conversations
- Semantic search
- Audio concatenation
- Vector store

---

## 📋 Before You Start (5 minutes)

### Get These 2 API Keys:

**1. Google Gemini API Key** 🔑
```
→ Go to: https://makersuite.google.com/app/apikey
→ Click: "Create API Key"
→ Copy and save it
```

**2. Adobe PDF Embed Client ID** 🔑
```
→ Go to: https://developer.adobe.com/console
→ Create new project
→ Add: "PDF Embed API"
→ Copy the Client ID
```

---

## 🚀 Part 1: Deploy Backend (10 minutes)

### Step 1: Go to Render
```
→ Visit: https://dashboard.render.com
→ Sign up with GitHub (recommended)
```

### Step 2: Create Web Service
```
→ Click: "New +" button
→ Select: "Web Service"
→ Click: "Connect GitHub" (if first time)
→ Select your "DocaCast" repository
→ Click: "Connect"
```

### Step 3: Configure Service
Fill in these settings:

```
Name: docacast-backend
Environment: Python 3
Region: [Choose closest to you]
Branch: main

Root Directory: [leave blank]

Build Command:
pip install -r backend/requirements.txt

Start Command:
cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT

Instance Type: Free
```

### Step 4: Add Environment Variables
Scroll down → Click "Advanced" → Add these variables:

```
GOOGLE_API_KEY
Value: [paste your Google API key]

GEMINI_API_KEY  
Value: [paste same Google API key]

TTS_PROVIDER
Value: gemini

GEMINI_VOICE_A
Value: Charon

GEMINI_VOICE_B
Value: Aoede

PYTHON_VERSION
Value: 3.11.0
```

### Step 5: Deploy
```
→ Click: "Create Web Service"
→ Wait: 5-8 minutes for deployment
→ Copy your backend URL (looks like: https://docacast-backend-xxxx.onrender.com)
```

**✅ Backend Done! Note your URL, you'll need it next.**

---

## 🎨 Part 2: Deploy Frontend (10 minutes)

### Step 1: Update Local Configuration

Open PowerShell in your DocaCast folder:

```powershell
# Create frontend env file
cd frontend/pdf-reader-ui
New-Item -Path .env -ItemType File -Force

# Open in notepad
notepad .env
```

Add these lines (replace with your values):
```env
VITE_API_BASE_URL=https://your-backend-url.onrender.com
VITE_ADOBE_CLIENT_ID=your_adobe_client_id_here
```

Save and close.

### Step 2: Commit Changes

```powershell
# Go back to project root
cd ../..

# Add and commit
git add .
git commit -m "Configure for production deployment"
git push origin main
```

### Step 3: Deploy on Vercel

```
→ Visit: https://vercel.com/dashboard
→ Click: "Add New..." → "Project"
→ Click: "Import Git Repository"
→ Authorize Vercel to access GitHub (if first time)
→ Select: "DocaCast" repository
→ Click: "Import"
```

### Step 4: Configure Vercel Project

Settings should auto-fill, but verify:

```
Framework Preset: Vite ✅

Root Directory: ./ ✅

Build Command:
cd frontend/pdf-reader-ui && npm install && npm run build

Output Directory:
frontend/pdf-reader-ui/dist
```

### Step 5: Add Environment Variables

Scroll to "Environment Variables":

```
Name: VITE_API_BASE_URL
Value: https://your-backend-url.onrender.com
Environments: ✅ Production ✅ Preview ✅ Development

Name: VITE_ADOBE_CLIENT_ID
Value: [your Adobe client ID]
Environments: ✅ Production ✅ Preview ✅ Development
```

### Step 6: Deploy

```
→ Click: "Deploy"
→ Wait: 2-3 minutes
→ Click: "Visit" when ready
```

**✅ Frontend Done! Your app is live!**

---

## 🧪 Part 3: Test Your App (5 minutes)

### Visit Your App
```
Your URL: https://your-app-name.vercel.app
```

### Test Workflow:

1. **Upload PDF**
   - Click "Upload PDF" button
   - Select a small PDF (2-3 pages for first test)
   - Wait for upload

2. **View PDF**
   - PDF should display in Adobe viewer
   - Try navigating pages

3. **Generate Podcast**
   - Click "Generate Podcast" button
   - Select "Two Speakers" mode
   - Click "Generate"
   - Wait 30-90 seconds (first request takes longer)

4. **Listen to Audio**
   - Audio player should appear
   - Click play
   - Hear the AI-generated conversation!

**🎉 If all works → You're done! Celebrate!**

---

## ⚠️ First Request Notes

**Important:** The backend on Render free tier:
- Sleeps after 15 minutes of inactivity
- Takes 30-60 seconds to wake up
- Subsequent requests are fast

**First Generation Tips:**
- Use a small PDF (2-3 pages)
- Wait patiently for cold start
- Don't refresh the page
- Check browser console if issues

---

## 🆘 Troubleshooting

### Backend Health Check

Visit: `https://your-backend-url.onrender.com/v1/health`

Should see:
```json
{"status":"ok"}
```

If not:
1. Check Render logs: Dashboard → Your Service → Logs
2. Verify environment variables are set
3. Check build logs for errors

### Frontend Issues

**"Cannot reach API"**
1. Check `VITE_API_BASE_URL` is correct in Vercel
2. Test backend health endpoint
3. Check browser console (F12) for errors

**"PDF won't upload"**
1. Try a smaller PDF (< 5MB)
2. Check if PDF is corrupted
3. Look at network tab in browser dev tools

**"Audio generation fails"**
1. Verify `GOOGLE_API_KEY` in Render
2. Check Render logs for errors
3. Ensure API key has Gemini enabled
4. Try a shorter document

### Getting Logs

**Render Backend:**
```
→ Dashboard → docacast-backend → Logs tab
→ Watch for errors in real-time
```

**Vercel Frontend:**
```
→ Dashboard → Your Project → Deployments
→ Click latest deployment → View Function Logs
```

---

## 🎯 Quick Commands Reference

### Redeploy Frontend
```powershell
git add .
git commit -m "Update"
git push origin main
# Vercel auto-deploys
```

### Redeploy Backend
```
→ Render Dashboard → Your Service → Manual Deploy
→ Or push to GitHub (auto-deploy enabled)
```

### View Logs
```powershell
# Vercel CLI (optional)
npx vercel logs

# Or use web dashboard
```

---

## 📊 What You Got

```
✅ Frontend: https://your-app.vercel.app
✅ Backend: https://your-backend.onrender.com
✅ Cost: $0/month
✅ Features: 100% working
✅ HTTPS: Automatic
✅ CDN: Automatic (Vercel)
✅ Auto-deploy: Push to GitHub
```

---

## 🚀 Next Steps

### Now That You're Live:

1. **Share Your App**
   - Send link to friends
   - Test with different PDFs
   - Get feedback

2. **Monitor Usage**
   - Check Render metrics
   - Check Vercel analytics
   - Watch for errors

3. **Consider Upgrade**
   - If cold starts annoying → Railway ($5/month)
   - If need more storage → Render paid tier
   - If high traffic → Scale up

4. **Customize**
   - Add your own branding
   - Customize voices
   - Add features

---

## 💡 Pro Tips

✅ **Test locally first**
```powershell
# Backend
cd backend
uvicorn main:app --reload

# Frontend (new terminal)
cd frontend/pdf-reader-ui
npm run dev
```

✅ **Keep API keys safe**
- Never commit to Git
- Use environment variables only
- Rotate keys regularly

✅ **Start small**
- Test with 2-3 page PDFs first
- Check logs frequently
- Fix issues before scaling

✅ **Monitor costs**
- Render free: 750 hours/month
- Google Gemini: Check quota
- Adobe Embed: Free tier generous

---

## 🎉 Success!

If you've followed all steps, you now have:

- ✅ Fully deployed DocaCast
- ✅ All features working
- ✅ Professional URLs
- ✅ Automatic deployments
- ✅ Zero cost

**Share your creation and enjoy! 🎙️✨**

---

## 📞 Need Help?

1. Check logs (Render + Vercel)
2. Read `DEPLOYMENT_GUIDE_FULL.md` for details
3. Create issue on GitHub
4. Check platform docs:
   - Render: https://render.com/docs
   - Vercel: https://vercel.com/docs

---

**Total Time: ~20 minutes | Total Cost: $0 | All Features: Working ✅**

**Ready? Open Render and Vercel, and let's deploy! 🚀**
