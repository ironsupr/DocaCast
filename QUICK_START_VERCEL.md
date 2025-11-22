# 🎯 Quick Start - Deploy to Vercel in 5 Minutes

This is the **fastest way** to get DocaCast running on Vercel!

## 🚦 Before You Start (2 minutes)

### Get Your API Keys:

1. **Google Gemini API Key** 🔑
   - Go to: https://makersuite.google.com/app/apikey
   - Click "Create API Key"
   - Copy the key
   
2. **Adobe PDF Embed Client ID** 🔑
   - Go to: https://developer.adobe.com/console
   - Create a new project
   - Add "PDF Embed API"
   - Copy the Client ID

## 🚀 Deploy in 3 Steps (3 minutes)

### Step 1: Import to Vercel

1. Go to: **https://vercel.com/dashboard**
2. Click: **"Add New..." → "Project"**
3. Click: **"Import Git Repository"**
4. Select your DocaCast repository
5. Click: **"Import"**

### Step 2: Add Environment Variables

In the "Configure Project" page, scroll to **Environment Variables**:

Add these two variables:

```
Key: GOOGLE_API_KEY
Value: [paste your Google API key]
Environments: ✅ Production ✅ Preview ✅ Development

Key: VITE_ADOBE_CLIENT_ID  
Value: [paste your Adobe Client ID]
Environments: ✅ Production ✅ Preview ✅ Development
```

### Step 3: Deploy!

1. Click: **"Deploy"**
2. Wait 2-3 minutes ⏳
3. Click: **"Visit"** when done ✅

## 🎉 You're Live!

Your DocaCast is now running at: `https://your-app.vercel.app`

### Test It:

1. Upload a PDF document
2. Click "Generate Podcast"
3. Listen to your AI-generated podcast! 🎙️

## 🔧 Optional Configuration

Want to customize? Add these optional environment variables:

```
TTS_PROVIDER=gemini                    # Voice engine
GEMINI_VOICE_A=Charon                  # Speaker 1 voice
GEMINI_VOICE_B=Aoede                   # Speaker 2 voice
```

## 🆘 Something Not Working?

### Common Issues:

**"API key invalid"**
- Double-check your GOOGLE_API_KEY
- Make sure Gemini API is enabled

**"PDF won't upload"**
- Check browser console for errors
- Verify file size is under 10MB

**"Audio won't generate"**
- Check Vercel function logs
- Verify environment variables are set

**"404 errors"**
- Redeploy the project
- Check vercel.json configuration

### Need More Help?

- 📖 [Full Deployment Guide](VERCEL_DEPLOYMENT.md)
- ✅ [Pre-Deployment Checklist](DEPLOYMENT_CHECKLIST.md)
- 🐛 [Report an Issue](https://github.com/ironsupr/DocaCast/issues)

## 📊 Next Steps

Now that you're deployed:

1. **Custom Domain**: Add your own domain in Vercel settings
2. **Monitoring**: Check analytics in Vercel dashboard
3. **Updates**: Push to GitHub to auto-deploy changes

## 💡 Pro Tips

- 🎯 **Test locally first** before deploying
- 🔒 **Never commit API keys** to Git
- 📈 **Monitor usage** to avoid quota limits
- 🚀 **Use preview deployments** for testing changes

---

**That's it! Enjoy your AI-powered podcast generator! 🎙️✨**

### Share Your Creation

- Tweet: "Just deployed #DocaCast on @vercel! 🎙️"
- Star the repo: https://github.com/ironsupr/DocaCast
- Share with friends!
