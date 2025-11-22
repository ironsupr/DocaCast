# Vercel Environment Variables Setup

## Required Environment Variables

Go to your Vercel project settings: https://vercel.com/your-username/docacast-frontend/settings/environment-variables

Add the following environment variable:

### `VITE_API_BASE_URL`
- **Value**: `https://docacast-backend.onrender.com`
- **Environment**: Production, Preview, Development (select all)
- **Description**: Backend API URL for DocaCast

### `VITE_ADOBE_CLIENT_ID`
- **Value**: `81899a7d32be4f8bb2bde1329810a497`
- **Environment**: Production, Preview, Development (select all)
- **Description**: Adobe PDF Embed API client ID

## After Setting Environment Variables

1. Go to the Deployments tab
2. Find the latest deployment
3. Click the three dots menu (⋯)
4. Click "Redeploy"
5. Select "Use existing Build Cache" (optional)
6. Click "Redeploy"

This will rebuild the frontend with the correct environment variables.

## Verification

After redeployment, open the browser console on your site and run:
```javascript
// This should show your backend URL
console.log(import.meta.env.VITE_API_BASE_URL)
```

Or check the Network tab when uploading a file - the request should go to:
```
https://docacast-backend.onrender.com/upload
```

Not to:
```
https://doca-cast.vercel.app/api/upload  ❌ WRONG
```
