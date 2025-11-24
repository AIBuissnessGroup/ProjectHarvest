# Project Harvest

AI-powered analytics platform for Fortnite Creative map activations. Built in collaboration between University of Michigan AI Business Group and Cherry Pick Talent.

![Project Harvest](harvest-ui/public/harvest-logo.png)

---

## 🚀 Quick Start

### Prerequisites
- **Node.js** 18+ (for frontend)
- **Python** 3.11+ (for backend)
- **Docker** (optional, for containerized deployment)

---

## 🎯 Running the Full Stack

### 1. Start the Backend API

```bash
cd project-harvest-backend

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# Run the FastAPI server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Backend will be available at: **http://localhost:8000**
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### 2. Start the Frontend

```bash
cd harvest-ui

# Install dependencies (first time only)
npm install
# or
pnpm install

# Create environment file
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Run the development server
npm run dev
# or
pnpm dev
```

Frontend will be available at: **http://localhost:3000**

---

## 🐳 Docker Deployment (Alternative)

Run the entire backend stack with one command:

```bash
cd project-harvest-backend

# Create .env file with your settings
cp .env.example .env

# Start all services (API, Redis, PostgreSQL, Jupyter)
docker-compose up --build

# Stop services
docker-compose down
```

---

## 🤖 Features

### **AI-Powered Analytics**
- **Future CCU Prediction** - Predict map performance 7 days ahead with daily breakdowns
- **Anomaly Detection** - Identify unusual spikes from campaigns or viral moments
- **Discovery Predictor** - Assess probability of hitting Fortnite Discovery placement
- **AI Chatbot** - Natural language interface powered by Google Gemini

### **Data Sources**
- Real-time map data from [fncreate.gg](https://fncreate.gg)
- 962+ Fortnite Creative maps in training dataset
- Live CCU tracking and historical analysis

### **ML Models**
1. **Future CCU Predictor** (R² = 0.76)
   - Gradient Boosting Regressor
   - Predicts 7-day future CCU
   - Daily breakdown with confidence intervals

2. **Anomaly Detector**
   - Isolation Forest + Statistical Analysis
   - Campaign spike detection
   - Timestamp identification

3. **Discovery Predictor** (AUC = 0.82)
   - Random Forest Classifier
   - Probability scoring
   - Actionable recommendations

---

## 📁 Project Structure

```
project-harvest/
├── harvest-ui/              # Next.js frontend
│   ├── src/
│   │   ├── app/            # Pages (Home, Analyzer)
│   │   ├── components/     # React components
│   │   ├── lib/            # API client, utilities
│   │   └── hooks/          # Custom React hooks
│   └── package.json
│
├── project-harvest-backend/ # FastAPI backend
│   ├── app/
│   │   ├── api/           # API routes
│   │   ├── services/      # ML, Chat, Data services
│   │   ├── models/        # Pydantic models
│   │   └── core/          # Configuration
│   ├── data/
│   │   ├── raw/           # Training data (962 maps)
│   │   └── models/        # Trained ML models
│   ├── notebooks/         # Jupyter notebooks
│   ├── docker-compose.yml
│   └── requirements.txt
│
└── README.md              # This file
```

---

## 🔧 API Endpoints

### Analytics
- `POST /api/v1/analytics/predict/future-ccu` - 7-day CCU forecast
- `POST /api/v1/analytics/detect/anomalies` - Spike detection
- `POST /api/v1/analytics/predict/discovery` - Discovery probability
- `GET /api/v1/analytics/model-info` - Model metadata

### Chat (AI Assistant)
- `POST /api/v1/chat` - Send message to AI
- `POST /api/v1/chat/insights/{map_code}` - Get map insights
- `POST /api/v1/chat/compare` - Compare multiple maps
- `GET /api/v1/chat/health` - Chat service health

### Maps
- `GET /api/v1/islands/{map_code}` - Get map details

---

## 🎨 Tech Stack

### Frontend
- **Next.js 16** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Radix UI** - Component library
- **Lucide React** - Icons
- **Recharts** - Data visualization

### Backend
- **FastAPI** - Python web framework
- **Google Gemini AI** - Conversational AI
- **Scikit-learn** - Machine learning
- **Redis** - Caching layer
- **PostgreSQL** - Database (optional)
- **Docker** - Containerization

---

## 📊 Example Usage

### Using the Chat Interface

1. Open the Analyzer page: http://localhost:3000/analyzer
2. Try these commands:

```
Predict the future CCU for map 8530-0110-2817

Compare maps 8530-0110-2817 and 8942-4322-3496

Detect anomalies for map 8530-0110-2817

What is the Discovery probability for map 8530-0110-2817?
```

### Direct API Usage

```bash
# Future CCU Prediction
curl -X POST "http://localhost:8000/api/v1/analytics/predict/future-ccu" \
  -H "Content-Type: application/json" \
  -d '{"map_code": "8530-0110-2817"}'

# Chat with AI
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Predict CCU for map 8530-0110-2817", "conversation_history": []}'
```

---

## 🔑 Environment Variables

### Backend (`.env`)
```env
# Google Gemini API Key (required for chat)
GEMINI_API_KEY=your_api_key_here

# Database (optional)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=harvest
POSTGRES_USER=harvest_user
POSTGRES_PASSWORD=your_password

# Redis (optional)
REDIS_HOST=localhost
REDIS_PORT=6379
CACHE_TTL=3600

# API Settings
API_V1_STR=/api/v1
PROJECT_NAME=Project Harvest API
DEBUG=True
```

### Frontend (`.env.local`)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 🧪 Development

### Retrain ML Models
```bash
cd project-harvest-backend

# Start Jupyter
jupyter notebook notebooks/

# Open and run:
# - train_future_ccu_model.ipynb
# - train_anomaly_detector.ipynb
# - train_discovery_predictor.ipynb
```

### Add New Map Data
```bash
cd project-harvest-backend
python scripts/fetch_paginated_maps.py
```

---

## 🤝 Contributing

This project is a collaboration between:
- **University of Michigan AI Business Group** - ML/AI Development
- **Cherry Pick Talent** - Product Strategy & Requirements
- **Epic Games** - Data Partnership

---

## 📄 License

Proprietary - All rights reserved.

---

## 🆘 Troubleshooting

### Backend won't start
```bash
# Make sure Python packages are installed
pip install -r requirements.txt

# Check if port 8000 is available
lsof -ti:8000 | xargs kill -9
```

### Frontend can't connect to backend
```bash
# Verify backend is running
curl http://localhost:8000/health

# Check .env.local file exists
cat harvest-ui/.env.local
```

### Chat returns errors
```bash
# Verify Gemini API key is set
grep GEMINI_API_KEY project-harvest-backend/.env

# Test chat endpoint directly
curl http://localhost:8000/api/v1/chat/health
```

---

## 📞 Support

For questions or issues, contact the development team or open an issue in the repository.

**Built with ❤️ by the Project Harvest Team**

