# 📋 Pre-Deployment Checklist for Vercel

Before deploying to Vercel, make sure you have completed all these steps:

## ✅ Repository Preparation

- [ ] All changes committed to Git
- [ ] `.gitignore` is properly configured
- [ ] No sensitive data (API keys, credentials) in the repository
- [ ] `vercel.json` configuration file is present
- [ ] `api/` folder with serverless functions is ready

## ✅ Required API Keys & Credentials

- [ ] **Google API Key** (Gemini AI)
  - Get from: https://makersuite.google.com/app/apikey
  - Enable Gemini API in Google Cloud Console
  
- [ ] **Adobe PDF Embed Client ID**
  - Get from: https://developer.adobe.com/console
  - Create a new project and generate credentials

## ✅ Environment Variables to Set in Vercel

Copy these to Vercel's environment variables section:

### Required:
```
GOOGLE_API_KEY=<your_google_api_key>
VITE_ADOBE_CLIENT_ID=<your_adobe_client_id>
```

### Optional (with defaults):
```
TTS_PROVIDER=gemini
GEMINI_VOICE_A=Charon
GEMINI_VOICE_B=Aoede
```

## ✅ Build Configuration

Verify these settings in Vercel dashboard:

- [ ] **Framework Preset**: Vite
- [ ] **Root Directory**: `./` (leave as root)
- [ ] **Build Command**: `cd frontend/pdf-reader-ui && npm install && npm run build`
- [ ] **Output Directory**: `frontend/pdf-reader-ui/dist`
- [ ] **Install Command**: `pip install -r api/requirements.txt`

## ✅ Testing Before Deployment

Test locally first:

```bash
# Backend
cd backend
uvicorn main:app --reload --host 127.0.0.1 --port 8001

# Frontend (in a new terminal)
cd frontend/pdf-reader-ui
npm run dev
```

Test these features:
- [ ] Upload a PDF
- [ ] View PDF in Adobe viewer
- [ ] Generate audio (single speaker)
- [ ] Generate podcast (two speakers)
- [ ] Search functionality

## ✅ Files to Verify

Make sure these files exist and are correct:

```
DocaCast/
├── vercel.json                           ✓ Configuration
├── VERCEL_DEPLOYMENT.md                  ✓ Deployment guide
├── api/
│   ├── generate-audio.py                 ✓ Serverless function
│   ├── upload.py                         ✓ Serverless function
│   ├── search.py                         ✓ Serverless function
│   ├── health.py                         ✓ Serverless function
│   └── requirements.txt                  ✓ Python dependencies
├── frontend/pdf-reader-ui/
│   ├── package.json                      ✓ Node dependencies
│   ├── vite.config.ts                    ✓ Vite configuration
│   └── src/utils/api.ts                  ✓ API configuration
└── backend/
    └── (for local development only)
```

## 🚀 Ready to Deploy?

If all boxes are checked, you're ready to deploy!

### Quick Deploy Steps:

1. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Ready for Vercel deployment"
   git push origin main
   ```

2. **Go to Vercel**:
   - Visit https://vercel.com/dashboard
   - Click "Add New..." → "Project"
   - Import your GitHub repository
   - Configure environment variables
   - Click "Deploy"

3. **Wait for Deployment** (2-5 minutes)

4. **Test Your Live App**:
   - Visit the deployment URL
   - Test uploading a PDF
   - Test generating audio

## 🆘 Common Issues

### Build Fails
- Check build logs for specific errors
- Verify all dependencies are listed in requirements.txt and package.json
- Make sure .gitignore doesn't exclude necessary files

### API Not Working
- Verify environment variables are set correctly
- Check that `vercel.json` rewrites are configured
- Look at runtime logs for errors

### Audio Generation Fails
- Verify GOOGLE_API_KEY is valid and has Gemini API enabled
- Check TTS_PROVIDER is set correctly
- Ensure API quota isn't exceeded

## 📞 Need Help?

- Read: [VERCEL_DEPLOYMENT.md](./VERCEL_DEPLOYMENT.md) for detailed guide
- Check: [Vercel Documentation](https://vercel.com/docs)
- Ask: Create an issue on GitHub

---

**Good luck with your deployment! 🎉**
