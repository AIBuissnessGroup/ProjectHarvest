# Project Harvest - Fortnite Activation Analytics Platform

A comprehensive analytics dashboard for tracking Fortnite map activations, combining in-game performance metrics with external social media engagement data.

## 🎯 Project Overview

**Project Harvest** is a collaborative research initiative between:
- **Cherry Pick Talent** (Epic Games Fortnite Map Activations)
- **University of Michigan - AI Business Group**

The platform provides real-time tracking and analysis of Fortnite map activations, correlating internal metrics (CCU, discovery panels, retention) with external social media signals (Twitter, TikTok, YouTube, Instagram).

## ✨ Features

### 🤖 AI-Powered Chatbot Interface
- Cursor-like sidebar interface for natural language queries
- Real-time analysis of map performance and social trends
- Interactive data exploration through conversational AI

### 📊 Comprehensive Dashboard
- **Real-time Metrics**: Live CCU, retention rates, and engagement data
- **Social Media Analytics**: Cross-platform mention tracking and sentiment analysis
- **Performance Trends**: Historical data visualization and trend analysis
- **Top Performing Maps**: Leaderboard of successful activations

### 🎨 Modern UI/UX
- Dark theme optimized for data visualization
- Responsive design for all screen sizes
- Smooth animations and transitions
- Professional Fortnite-themed branding

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ 
- pnpm (recommended) or npm

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd harvest-ui
   ```

2. **Install dependencies**
   ```bash
   pnpm install
   ```

3. **Start the development server**
   ```bash
   pnpm dev
   ```

4. **Open your browser**
   Navigate to [http://localhost:3000](http://localhost:3000)

### Docker Setup

1. **Build and run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

2. **Or build the Docker image manually**
   ```bash
   docker build -t harvest-ui .
   docker run -p 3000:3000 harvest-ui
   ```

## 🛠️ Tech Stack

- **Frontend**: Next.js 16, React 19, TypeScript
- **Styling**: Tailwind CSS v3, Radix UI components
- **Icons**: Lucide React
- **Charts**: Recharts
- **State Management**: Zustand
- **Containerization**: Docker, Docker Compose

## 📁 Project Structure

```
src/
├── app/                 # Next.js app router
│   ├── globals.css     # Global styles
│   ├── layout.tsx      # Root layout
│   └── page.tsx        # Main dashboard page
├── components/
│   └── ui/             # Reusable UI components
└── lib/
    └── utils.ts        # Utility functions
```

## 🎮 Key Features Explained

### Dashboard Overview
- **Active Maps**: Current number of live Fortnite maps
- **Total CCU**: Concurrent users across all tracked maps
- **Social Mentions**: Cross-platform social media activity
- **Engagement Rate**: Overall user engagement metrics

### AI Assistant
The chatbot interface allows users to:
- Query specific map performance data
- Analyze social media trends
- Generate insights and reports
- Explore correlations between in-game and social metrics

### Data Visualization
- Interactive charts for map performance trends
- Social media activity progress bars
- Top performing maps leaderboard
- Real-time data updates

## 🔮 Future Enhancements

- **FastAPI Backend**: Python-based API for data processing
- **Real-time Data**: WebSocket connections for live updates
- **Advanced Analytics**: Machine learning insights and predictions
- **Report Generation**: Automated PDF and CSV report exports
- **Multi-language Support**: Internationalization for global teams

## 🤝 Contributing

This is a research project in collaboration with University of Michigan's AI Business Group. For contribution guidelines, please contact the project maintainers.

## 📄 License

This project is part of a collaborative research initiative. Please refer to the project documentation for licensing details.

## 🏫 University of Michigan AI Business Group

Powered by the University of Michigan's AI Business Group, bringing cutting-edge AI research to the gaming industry.

---

**Project Harvest** - Transforming Fortnite activation analytics through AI-powered insights.
