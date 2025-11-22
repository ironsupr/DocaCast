# 🚀 Vercel Deployment Guide for DocaCast

This guide will walk you through deploying DocaCast on Vercel using the web interface.

## Prerequisites

Before you begin, make sure you have:

1. ✅ A [Vercel account](https://vercel.com/signup) (free tier works!)
2. ✅ Your GitHub/GitLab/Bitbucket repository URL
3. ✅ **Google API Key** (Gemini AI) - [Get it here](https://makersuite.google.com/app/apikey)
4. ✅ **Adobe PDF Embed Client ID** - [Get it here](https://developer.adobe.com/document-services/apis/pdf-embed/)

## Step-by-Step Deployment from Vercel Website

### Step 1: Prepare Your Repository

1. **Commit all your changes** to Git:
   ```bash
   git add .
   git commit -m "Prepare for Vercel deployment"
   git push origin main
   ```

2. **Ensure these files are in your repository**:
   - ✅ `vercel.json` (configuration file)
   - ✅ `api/` folder with serverless functions
   - ✅ `frontend/pdf-reader-ui/` with React app

### Step 2: Import Project to Vercel

1. **Go to [Vercel Dashboard](https://vercel.com/dashboard)**

2. **Click "Add New..." → "Project"**

3. **Import Your Repository**:
   - If first time: Click "Add GitHub Account" or "Add GitLab" or "Add Bitbucket"
   - Authorize Vercel to access your repositories
   - Search for "DocaCast" or your repository name
   - Click "Import"

### Step 3: Configure Project Settings

On the "Configure Project" page:

#### **Framework Preset**
- Select: **Vite** (should auto-detect)

#### **Root Directory**
- Leave as: **`./`** (root)

#### **Build Settings**
The settings should auto-populate from `vercel.json`, but verify:

- **Build Command**: 
  ```
  cd frontend/pdf-reader-ui && npm install && npm run build
  ```

- **Output Directory**: 
  ```
  frontend/pdf-reader-ui/dist
  ```

- **Install Command**: 
  ```
  pip install -r api/requirements.txt
  ```

### Step 4: Configure Environment Variables

This is the **most critical step**! Click "Environment Variables" and add:

#### Required Variables:

| Variable Name | Value | Where to Get It |
|--------------|-------|-----------------|
| `GOOGLE_API_KEY` | Your Google Gemini API key | [Google AI Studio](https://makersuite.google.com/app/apikey) |
| `VITE_ADOBE_CLIENT_ID` | Your Adobe client ID | [Adobe Developer Console](https://developer.adobe.com/console) |
| `VITE_API_BASE_URL` | Leave empty or use `https://your-app.vercel.app` | Auto-configured |

#### Optional Variables (for enhanced features):

| Variable Name | Default | Description |
|--------------|---------|-------------|
| `TTS_PROVIDER` | `gemini` | TTS engine: `gemini`, `edge_tts`, `google`, `hf_dia` |
| `GEMINI_API_KEY` | Same as GOOGLE_API_KEY | Can be separate if needed |
| `GEMINI_VOICE_A` | `Charon` | First speaker voice |
| `GEMINI_VOICE_B` | `Aoede` | Second speaker voice |
| `HUGGINGFACE_API_TOKEN` | - | For HuggingFace TTS (optional) |

**For each variable:**
1. Enter the variable name in "Key"
2. Enter the value in "Value"
3. Select environments: ✅ Production, ✅ Preview, ✅ Development
4. Click "Add"

### Step 5: Deploy

1. **Click "Deploy"** button
2. Wait for the build process (usually 2-5 minutes)
3. Watch the build logs for any errors

### Step 6: Verify Deployment

Once deployed, you'll see:
- ✅ **Deployment URL** (e.g., `https://docacast-abc123.vercel.app`)
- ✅ Green "Ready" status

**Test your deployment:**
1. Click "Visit" to open your app
2. Try uploading a small PDF
3. Generate a podcast to test the API

## 🎯 Post-Deployment Configuration

### Update Frontend API URL (if needed)

If your frontend can't reach the API:

1. Go to your Vercel project settings
2. Add/update environment variable:
   ```
   VITE_API_BASE_URL = https://your-actual-domain.vercel.app
   ```
3. Redeploy (Vercel will auto-redeploy)

### Custom Domain (Optional)

1. Go to Project Settings → Domains
2. Click "Add Domain"
3. Enter your custom domain (e.g., `docacast.yourdomain.com`)
4. Follow DNS configuration instructions

## 🔧 Troubleshooting

### Build Fails

**Error: "Python module not found"**
- Solution: Ensure `api/requirements.txt` is correct
- Check build logs for specific missing modules

**Error: "npm install failed"**
- Solution: Delete `package-lock.json`, regenerate locally, commit and push

**Error: "Exceeded file size limit"**
- Solution: Check `.gitignore` to exclude large files
- Remove `node_modules/` from git if accidentally committed

### API Not Working

**Error: "API calls return 404"**
- Solution: Check `vercel.json` rewrites configuration
- Ensure API functions are in `api/` folder

**Error: "CORS errors"**
- Solution: Add CORS headers in `vercel.json` (already configured)
- Check if `Access-Control-Allow-Origin` is set correctly

**Error: "Missing environment variables"**
- Solution: Go to Project Settings → Environment Variables
- Add all required variables
- Redeploy after adding variables

### Audio Generation Fails

**Error: "TTS model not available"**
- Solution: Check `GOOGLE_API_KEY` is correctly set
- Verify API key has Gemini API enabled
- Try setting `TTS_PROVIDER=gemini` explicitly

**Error: "Serverless function timeout"**
- Solution: Vercel has 10s timeout on free tier (60s on Pro)
- For long PDFs, consider upgrading or processing in chunks

## 🚀 Continuous Deployment

Once set up, Vercel automatically:
- ✅ Deploys on every push to `main` branch
- ✅ Creates preview deployments for pull requests
- ✅ Provides deployment logs and analytics

To deploy updates:
```bash
git add .
git commit -m "Your update message"
git push origin main
```

Vercel will automatically build and deploy!

## 📊 Monitoring Your Deployment

### View Logs
1. Go to Vercel Dashboard → Your Project
2. Click on a deployment
3. View "Build Logs" and "Runtime Logs"

### Performance Analytics
1. Go to Project → Analytics
2. View visitor stats, performance metrics

### Error Tracking
1. Go to Project → Logs
2. Filter by "Errors" to see runtime issues

## 🔒 Security Best Practices

1. **Never commit API keys** - Always use environment variables
2. **Rotate keys regularly** - Update in Vercel settings
3. **Use preview URLs** - Test changes before production
4. **Enable HTTPS only** - Vercel does this by default

## 💰 Cost Considerations

### Free Tier Includes:
- ✅ 100GB bandwidth/month
- ✅ 100 hours serverless function execution
- ✅ Automatic HTTPS
- ✅ Preview deployments

### Upgrade if You Need:
- More bandwidth
- Longer serverless timeouts (60s vs 10s)
- Priority support
- Advanced analytics

## 🆘 Need Help?

- **Vercel Docs**: https://vercel.com/docs
- **DocaCast Issues**: https://github.com/ironsupr/DocaCast/issues
- **Vercel Support**: https://vercel.com/support

## 🎉 Success Checklist

After deployment, verify:
- [ ] App loads at Vercel URL
- [ ] PDF upload works
- [ ] Audio generation works
- [ ] Adobe PDF viewer displays documents
- [ ] No console errors
- [ ] Environment variables are set
- [ ] API endpoints respond correctly

**Congratulations! Your DocaCast is now live! 🎙️**

---

## Quick Commands Reference

```bash
# Push to deploy
git push origin main

# View deployment status
vercel --prod

# Pull environment variables
vercel env pull

# View logs
vercel logs
```

For programmatic deployment using Vercel CLI, see the advanced section below.

---

## Advanced: Deploy via Vercel CLI (Optional)

If you prefer command-line deployment:

### Install Vercel CLI
```bash
npm install -g vercel
```

### Login
```bash
vercel login
```

### Deploy
```bash
cd DocaCast
vercel --prod
```

### Set Environment Variables
```bash
vercel env add GOOGLE_API_KEY production
vercel env add VITE_ADOBE_CLIENT_ID production
```

But the web interface is recommended for first-time deployment!
