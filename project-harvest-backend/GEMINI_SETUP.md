# 🤖 Google Gemini AI Setup

## Why Gemini?

**Free Tier Benefits:**
- ✅ **1500 requests/day** (completely free!)
- ✅ Fast response times
- ✅ Function calling support
- ✅ Perfect for prototypes and demos
- ✅ No credit card required

vs OpenAI ChatGPT (requires paid subscription)

---

## 🔑 Getting Your API Key

### Step 1: Get Gemini API Key (Free!)

1. Go to: **https://makersuite.google.com/app/apikey**
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Copy your key (looks like: `AIzaSyC...`)

### Step 2: Add to Environment

**Option A: Environment Variable (Recommended)**
```bash
export GEMINI_API_KEY="your_api_key_here"
```

**Option B: Create `.env` file**
```bash
# In project-harvest-backend directory
echo "GEMINI_API_KEY=your_api_key_here" > .env
```

---

## 📦 Installation

Install the Gemini package:

```bash
pip install google-generativeai
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

---

## ✅ Verify Setup

Start the server and check if AI chat is working:

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Look for this in the startup logs:
```
✅ Chat service initialized with Gemini
```

If you see:
```
⚠️  GEMINI_API_KEY not set. Chat service will not work.
```

Then you need to set the API key.

---

## 🎯 What Works with Gemini

### Available Functions

1. **Get Map Prediction**
   - User: "What's the predicted peak CCU for map 1832-0431-4852?"
   - Gemini triggers: `get_map_prediction("1832-0431-4852")`
   - Your ML model runs, Gemini explains results

2. **Compare Multiple Maps**
   - User: "Compare maps A, B, and C"
   - Gemini triggers: `compare_maps(["A", "B", "C"])`
   - Gets rankings, statistics, and insights

3. **Quick Insights**
   - User: "Give me insights for my map"
   - Gemini provides analysis and recommendations

---

## 🆓 Free Tier Limits

**Gemini 1.5 Flash (what we're using):**
- ✅ 1500 requests per day
- ✅ 1 million tokens per minute
- ✅ 15 requests per minute

**More than enough for a demo!**

To upgrade (if needed): https://ai.google.dev/pricing

---

## 🔧 Troubleshooting

**Error: "GEMINI_API_KEY not set"**
- Make sure you exported the environment variable
- Or created `.env` file with the key

**Error: "google.generativeai could not be resolved"**
```bash
pip install google-generativeai
```

**Error: "API key invalid"**
- Double-check your API key
- Make sure there are no extra spaces
- Get a new key if needed

---

## 🎨 Differences from OpenAI

| Feature | OpenAI GPT-4 | Google Gemini |
|---------|--------------|---------------|
| **Cost** | Paid only | FREE tier! |
| **Requests/day** | Pay per request | 1500 free |
| **Speed** | Slower | Faster |
| **Function calling** | ✅ | ✅ |
| **Quality** | Excellent | Very good |

**For this prototype, Gemini is perfect!** 🎯

---

## 📚 Documentation

- Gemini API Docs: https://ai.google.dev/docs
- Python SDK: https://github.com/google/generative-ai-python
- Function Calling Guide: https://ai.google.dev/docs/function_calling

---

**Ready to use!** Start the server and try asking questions about your maps! 🚀

