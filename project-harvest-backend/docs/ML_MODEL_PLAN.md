# Project Harvest - Multi-Model ML System Plan

## 🎯 Client Objective
Measure and predict the impact of influencer marketing campaigns on Fortnite Creative map performance.

---

## 📊 MODEL ARCHITECTURE (6 Models)

### **Model 1: Baseline Peak CCU Predictor** ✅ (Already Built)
**Purpose:** Predict expected peak CCU without any influencer activation  
**Use Case:** Establish baseline to measure campaign impact against

**Input Features:**
- Map type, tags, max_players
- Creator followers
- Version (update frequency)
- Base organic growth rate

**Output:** Predicted organic peak CCU

**Training Data:** 300-500 maps in 200-1K range (current client focus)

**Status:** ✅ IN PROGRESS (Current notebook)

---

### **Model 2: Campaign Impact Predictor** 🔥 (HIGH PRIORITY)
**Purpose:** Predict CCU lift from an influencer campaign

**Input Features:**
- **Influencer Data:** (Client will provide)
  - Platform (TikTok, YouTube, Twitch, Instagram, Snapchat)
  - Follower count
  - Average views/engagement rate
  - Content type (stream vs video vs post)
  - Post time/date
  - Stream duration (for live streamers)
  
- **Map Baseline:**
  - Current CCU before campaign
  - Historical average CCU
  - Creator followers
  - Map age (days since launch)

- **Campaign Timing:**
  - Day of week
  - Time of day
  - Days since map launch
  - Concurrent campaigns (if any)

**Output:** 
- Predicted CCU increase (absolute)
- Predicted CCU lift % (relative)
- Confidence interval

**Training Data Needed:**
- Historical campaign data: 100-200 campaigns with before/after metrics
- Client will provide: Influencer content links + performance data

**ML Approach:** 
- Regression model (Random Forest or XGBoost)
- Feature engineering: influencer engagement rate, platform multipliers
- Time-series context window (CCU 24h before campaign)

---

### **Model 3: Time-Series Anomaly Detector** 🔥 (HIGH PRIORITY)
**Purpose:** Detect CCU spikes and attribute them to campaigns

**Input Features:**
- Minute-by-minute or hourly CCU time series
- Campaign start times
- Day/time features (seasonality)
- Historical CCU patterns

**Output:**
- Anomaly score (is this spike unusual?)
- Likely cause (organic vs campaign-driven)
- Spike magnitude and duration

**Training Data Needed:**
- Time-series CCU data (we have 24h, 7d from fncreate.gg)
- Campaign timestamps (client will provide)

**ML Approach:**
- LSTM or Transformer for time-series prediction
- Prophet or ARIMA for baseline forecasting
- Anomaly = Actual CCU - Predicted baseline CCU

**Use Case:** Automatically flag when a campaign drives a CCU spike

---

### **Model 4: Discovery Trigger Probability** (MEDIUM PRIORITY)
**Purpose:** Predict if a campaign will trigger Fortnite Discovery placement

**Input Features:**
- Campaign-driven CCU increase
- Map age and current discovery status
- Historical discovery patterns
- Time in discovery vs CCU history

**Output:**
- Probability of triggering discovery (0-1)
- Expected time to trigger (hours/days)
- Expected discovery tier (e.g., "Featured" vs "Popular")

**Training Data Needed:**
- Maps with known discovery events (can extract from our data)
- CCU patterns before/during discovery
- 200-300 maps with discovery history

**ML Approach:**
- Binary classification (will trigger discovery: yes/no)
- Logistic Regression or Gradient Boosting

**Use Case:** Help client predict if campaign will lead to viral discovery

---

### **Model 5: Player Retention Predictor** (LOW PRIORITY - Needs Client Data)
**Purpose:** Predict 7-day retention impact from campaign

**Input Features:** (CLIENT MUST PROVIDE)
- Unique players before/after campaign
- Session count before/after campaign
- Average session duration
- Campaign characteristics (from Model 2)

**Output:**
- Predicted 7-day retention rate
- Predicted sessions per unique player
- Quality score (sticky vs one-time spike)

**Training Data Needed:**
- Client's player-level data (100+ campaigns)
- Retention curves before/after activations

**ML Approach:**
- Survival analysis or time-to-churn models
- Feature: campaign quality indicators

**Status:** ⏸️ BLOCKED - Requires client data integration

---

### **Model 6: Platform-Specific Multipliers** (MEDIUM PRIORITY)
**Purpose:** Quantify impact differences by platform and streamer type

**Input Features:**
- Platform (TikTok, YouTube, Twitch, Instagram, Snapchat)
- Content type (live stream vs video vs post)
- Audience demographics (if available)
- Time of day posted/streamed

**Output:**
- Platform effectiveness score (relative to baseline)
- Best time to post by platform
- Streamer-type affinity by map genre

**Training Data Needed:**
- 50+ campaigns per platform (300+ total campaigns)
- Cross-platform comparison data

**ML Approach:**
- Multi-level regression with platform as categorical feature
- A/B test statistical analysis
- Bayesian inference for small sample sizes

**Use Case:** Help client choose optimal platforms for each map type

---

## 🗄️ DATA REQUIREMENTS

### **What We Already Have:**
✅ Map metadata (type, tags, creator, etc.)  
✅ CCU time-series (24h, 7d) from fncreate.gg  
✅ Discovery status data  
✅ 962 maps across all ranges  

### **What Client Must Provide:**
❌ **Influencer Campaign Data:**
- Campaign dates/times
- Influencer content links
- Influencer stats (followers, engagement rate)
- Platform for each campaign

❌ **Player-Level Metrics:**
- Unique players (daily/weekly)
- Session counts
- Average session duration
- Favorites/bookmarks count
- Retention curves (D1, D7, D30)

❌ **Historical Campaign Performance:**
- Previous campaigns with before/after metrics
- 100-200 campaigns minimum for training

### **What We Can Scrape/Collect:**
- Social media metrics (YouTube views, TikTok likes) via APIs
- Streamer live status via Twitch/YouTube APIs
- Content post times from social platforms

---

## 📈 PHASED IMPLEMENTATION PLAN

### **Phase 1: Foundation** (Current Sprint)
**Goal:** Get baseline prediction working

1. ✅ Train Model 1 (Baseline Peak CCU) on 200-1K range
2. ✅ Achieve R² > 0.5 for client's activation tier
3. ✅ Save model and integrate into API

**Deliverable:** Working API endpoint for organic peak CCU prediction

---

### **Phase 2: Campaign Impact** (Next Sprint - Needs Client Data)
**Goal:** Build core influencer impact model

**Prerequisites:**
- Client provides 50-100 historical campaigns with:
  - Influencer details (platform, followers, link)
  - Campaign date/time
  - Before/after CCU data

**Tasks:**
1. Collect influencer metadata (scrape social stats)
2. Feature engineering for campaign data
3. Train Model 2 (Campaign Impact Predictor)
4. Build Model 3 (Time-Series Anomaly Detector)
5. Create before/after comparison visualizations

**Deliverable:** API endpoints for:
- `/api/v1/campaigns/predict-impact` - Predict campaign lift
- `/api/v1/campaigns/analyze/{campaign_id}` - Analyze completed campaign

---

### **Phase 3: Advanced Analytics** (Future Sprint)
**Goal:** Build discovery and retention models

**Prerequisites:**
- 200+ campaigns in dataset
- Client integrates player-level data

**Tasks:**
1. Train Model 4 (Discovery Trigger Probability)
2. Train Model 5 (Player Retention Predictor)
3. Train Model 6 (Platform-Specific Multipliers)
4. Build comprehensive dashboard with all insights

**Deliverable:** Full influencer marketing analytics platform

---

## 🔧 TECHNICAL ARCHITECTURE

### **Database Schema Updates:**

```sql
-- New table: campaigns
CREATE TABLE campaigns (
    id UUID PRIMARY KEY,
    map_code VARCHAR(20),
    influencer_name VARCHAR(255),
    platform VARCHAR(50), -- TikTok, YouTube, etc.
    content_url TEXT,
    post_datetime TIMESTAMP,
    follower_count INTEGER,
    avg_engagement_rate FLOAT,
    content_type VARCHAR(50), -- stream, video, post
    stream_duration_minutes INTEGER,
    before_ccu INTEGER,
    after_ccu INTEGER,
    ccu_lift_percent FLOAT,
    triggered_discovery BOOLEAN,
    created_at TIMESTAMP
);

-- New table: campaign_metrics (time-series)
CREATE TABLE campaign_metrics (
    id UUID PRIMARY KEY,
    campaign_id UUID REFERENCES campaigns(id),
    timestamp TIMESTAMP,
    ccu INTEGER,
    unique_players INTEGER,
    sessions INTEGER,
    avg_session_duration INTEGER
);
```

### **New API Endpoints:**

```python
# Campaign Impact Prediction
POST /api/v1/campaigns/predict-impact
Body: {
    "map_code": "6522-1299-1581",
    "influencer": {
        "platform": "TikTok",
        "followers": 2000000,
        "avg_engagement_rate": 0.05,
        "content_type": "video"
    },
    "post_time": "2025-11-25T15:00:00Z"
}
Response: {
    "predicted_ccu_lift": 250,
    "predicted_lift_percent": 35.2,
    "confidence_interval": [180, 320],
    "discovery_trigger_probability": 0.65
}

# Campaign Analysis (Completed)
GET /api/v1/campaigns/analyze/{campaign_id}
Response: {
    "campaign_id": "...",
    "actual_ccu_lift": 280,
    "vs_predicted": 12.0,  // % difference
    "spike_detected": true,
    "discovery_triggered": true,
    "retention_impact": {
        "d1_retention": 0.42,
        "d7_retention": 0.18
    },
    "roi_score": 8.5
}

# Platform Comparison
GET /api/v1/analytics/platform-performance?map_type=lego
Response: {
    "platforms": [
        {
            "platform": "TikTok",
            "avg_ccu_lift": 285,
            "cost_per_ccu": 2.50,
            "best_post_time": "15:00-18:00",
            "sample_size": 45
        },
        // ... other platforms
    ]
}
```

---

## 📊 DATA COLLECTION SCRIPTS TO BUILD

### **Script 1: `fetch_campaign_data.py`**
Collect influencer campaign data from client CSV/API

### **Script 2: `scrape_social_metrics.py`**
Scrape social platform metrics (YouTube API, TikTok API, etc.)

### **Script 3: `collect_campaign_timeseries.py`**
Fetch minute-by-minute CCU during campaign windows

### **Script 4: `enrich_campaign_features.py`**
Add derived features (engagement rate, platform multipliers, etc.)

---

## 🎯 SUCCESS METRICS

### **Model 1 (Baseline CCU):**
- Target R² > 0.5 for 200-1K range ✅
- MAE < 200 CCU

### **Model 2 (Campaign Impact):**
- Target R² > 0.6 for campaign lift prediction
- MAE < 100 CCU lift
- 80% of predictions within ±30% of actual

### **Model 3 (Anomaly Detection):**
- 90%+ accuracy detecting campaign-driven spikes
- False positive rate < 10%

### **Model 4 (Discovery Trigger):**
- AUC > 0.75 for binary classification
- Precision > 0.70 (when we say it will trigger, we're right 70%+ of the time)

---

## 💡 KEY INSIGHTS FOR CLIENT

1. **This is NOT a simple peak CCU prediction problem** - it's a causal inference + time-series problem
2. **We need their campaign data** - minimum 50-100 historical campaigns
3. **Player-level data is crucial** - for retention and engagement analysis
4. **Platform matters** - different platforms have different impact profiles
5. **Time-series analysis** - minute-level CCU data is more valuable than peak CCU
6. **Attribution is hard** - need to separate organic growth from campaign impact

---

## 🚀 IMMEDIATE NEXT STEPS

1. ✅ Finish Model 1 (current notebook) - get R² > 0.5
2. 📧 Request campaign data from client:
   - Historical campaigns CSV
   - Player metrics API access
   - Social media campaign links
3. 🔧 Build campaign data ingestion pipeline
4. 📊 Create campaign impact analysis notebook (Model 2)
5. 🎯 Focus on time-series analysis (Model 3) for spike detection

---

**This is a $100K+ analytics platform project, not a simple ML model!** 🚀

