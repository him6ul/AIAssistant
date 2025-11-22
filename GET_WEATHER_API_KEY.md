# How to Get OpenWeather API Key

## Step 1: Sign Up for Free Account

1. **Visit OpenWeather Sign-Up Page**:
   - Go to: https://home.openweathermap.org/users/sign_up
   - Fill out the registration form:
     - Username
     - Email address
     - Password
     - Confirm password
   - Click "Create Account"

2. **Verify Your Email**:
   - Check your email inbox
   - Click the verification link from OpenWeather
   - This activates your account

## Step 2: Get Your API Key

1. **Log In**:
   - Go to: https://home.openweathermap.org/
   - Log in with your credentials

2. **Access API Keys**:
   - Once logged in, you'll see your dashboard
   - Click on "API keys" in the top navigation
   - You'll see your default API key (it starts with letters/numbers)
   - **Copy this key** - you'll need it in the next step

## Step 3: Add API Key to Your Project

1. **Open your `.env` file**:
   ```bash
   cd /Users/himanshu/SourceCode/Personal/AI_Assistant
   nano .env
   # or use your preferred editor
   ```

2. **Add these lines**:
   ```bash
   OPENWEATHER_API_KEY=your_api_key_here
   DEFAULT_LOCATION=San Francisco
   ```

3. **Replace `your_api_key_here`** with the actual API key you copied

4. **Save the file**

## Step 4: Restart the Backend

After adding the API key, restart your backend:

```bash
# Stop the current backend
pkill -f "app.main"

# Start it again
./scripts/run_backend.sh
```

## Step 5: Test It

Try asking: "What is the weather?" or "What's the weather in New York?"

## Important Notes

- **Free Tier**: The free tier includes:
  - 60 calls/minute
  - 1,000,000 calls/month
  - Current weather data
  - 5-day/3-hour forecast

- **Activation Time**: Your API key may take **1-3 hours** to become active after creation

- **Rate Limits**: Be mindful of the rate limits (60 calls per minute)

## Troubleshooting

If weather commands don't work:

1. **Check API key is set**:
   ```bash
   grep OPENWEATHER_API_KEY .env
   ```

2. **Verify backend is running**:
   ```bash
   curl http://localhost:8000/health
   ```

3. **Check logs**:
   ```bash
   tail -f logs/assistant.log
   ```

4. **Test the API key directly**:
   ```bash
   curl "http://api.openweathermap.org/data/2.5/weather?q=San%20Francisco&appid=YOUR_API_KEY"
   ```

## Alternative: Use Without API Key

If you don't want to set up an API key right now, the assistant will respond with:
> "I can't check the weather right now. Please set OPENWEATHER_API_KEY in your .env file."

But it will still handle the command (just won't fetch actual weather data).

