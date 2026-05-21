# Social Authentication Setup Guide

This guide explains how to set up Google and Facebook OAuth for social login.

## Backend Setup

The backend is already configured to handle social authentication. You just need to add OAuth credentials.

## Frontend Setup

### 1. Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable Google+ API
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"
5. Configure OAuth consent screen if prompted
6. Add authorized redirect URIs:
   - `http://localhost:5173/auth/google/callback` (development)
   - `https://yourdomain.com/auth/google/callback` (production)
7. Copy the **Client ID**

### 2. Facebook OAuth Setup

1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Create a new app or select an existing one
3. Add "Facebook Login" product
4. Go to Settings → Basic
5. Add authorized redirect URIs:
   - `http://localhost:5173` (development)
   - `https://yourdomain.com` (production)
6. Copy the **App ID**

### 3. Environment Variables

Create or update `.env` file in the `frontend` directory:

```env
VITE_GOOGLE_CLIENT_ID=your_google_client_id_here
VITE_FACEBOOK_APP_ID=your_facebook_app_id_here
```

Or add to your Vite config if using a different setup.

## How It Works

1. **User clicks "Continue with Google" or "Continue with Facebook"**
2. **OAuth popup opens** - User authenticates with provider
3. **Access token received** - Frontend gets access token from provider
4. **Token sent to backend** - Backend verifies token and gets user info
5. **User created/logged in** - Backend creates user if new, or logs in existing user
6. **JWT token returned** - User is logged in with JWT token (same as regular login)

## Features

- ✅ Automatic user creation for new social logins
- ✅ Links existing accounts by email
- ✅ Works with existing JWT authentication system
- ✅ Phone number can be added later (placeholder used initially)
- ✅ Default user type: freelancer (can be changed in profile)

## Testing

1. Make sure environment variables are set
2. Start the frontend: `npm run dev`
3. Go to login page
4. Click "Continue with Google" or "Continue with Facebook"
5. Complete OAuth flow
6. User should be logged in automatically

## Notes

- Phone number is required but uses a placeholder for social auth users
- Users should update their phone number in profile after social login
- User type defaults to 'freelancer' but can be changed in profile
- Social auth uses the same JWT token system as regular login
