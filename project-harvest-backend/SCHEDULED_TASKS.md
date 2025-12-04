# Scheduled Tasks - Automated Data Collection & Model Training

This document explains the automated data collection and model retraining system.

## Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    AUTOMATED PIPELINE                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   DAILY (6 AM UTC)              WEEKLY (Sunday 7 AM UTC)    │
│   ┌─────────────────┐           ┌─────────────────┐         │
│   │ Collect CCU     │           │ Check new data  │         │
│   │ for all maps    │           │ (7+ days?)      │         │
│   └────────┬────────┘           └────────┬────────┘         │
│            │                             │                   │
│            ▼                             ▼                   │
│   ┌─────────────────┐           ┌─────────────────┐         │
│   │ Save to         │           │ Retrain models  │         │
│   │ data/historical │           │ if improved     │         │
│   └────────┬────────┘           └────────┬────────┘         │
│            │                             │                   │
│            ▼                             ▼                   │
│   ┌─────────────────┐           ┌─────────────────┐         │
│   │ Commit to       │           │ Deploy if       │         │
│   │ GitHub          │           │ R² improved 1%+ │         │
│   └─────────────────┘           └─────────────────┘         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Scripts

### 1. Daily Data Collection
**Script:** `scripts/collect_daily_ccu.py`

Collects CCU data for all tracked maps and saves daily snapshots.

```bash
# Run manually
python scripts/collect_daily_ccu.py

# Collect specific maps
python scripts/collect_daily_ccu.py --maps 8530-0110-2817,0038-9297-7629
```

**Output:**
- `data/historical/{map_code}/YYYY-MM-DD.json` - Daily snapshots
- `data/historical/_logs/collection_YYYY-MM-DD.json` - Collection logs

### 2. Automated Model Retraining
**Script:** `scripts/auto_retrain.py`

Checks if enough new data exists and retrains models if improvement is possible.

```bash
# Normal run (only retrains if 7+ new days)
python scripts/auto_retrain.py

# Force retrain
python scripts/auto_retrain.py --force

# Dry run (check without retraining)
python scripts/auto_retrain.py --dry-run
```

**Safeguards:**
- Only retrains if 7+ days of new data
- Only deploys if new model R² is 1%+ better
- Backs up current model before replacing

### 3. Unified Task Runner
**Script:** `scripts/scheduled_tasks.py`

Runs scheduled tasks with a single command.

```bash
python scripts/scheduled_tasks.py daily   # Run daily tasks
python scripts/scheduled_tasks.py weekly  # Run weekly tasks
python scripts/scheduled_tasks.py all     # Run all tasks
```

## GitHub Actions Schedule

The workflow runs automatically via GitHub Actions:

| Task | Schedule | Cron |
|------|----------|------|
| Daily collection | Every day 6 AM UTC | `0 6 * * *` |
| Weekly retrain | Sunday 7 AM UTC | `0 7 * * 0` |

### Manual Trigger

You can also run tasks manually:
1. Go to GitHub → Actions → "Scheduled Data Collection & Model Training"
2. Click "Run workflow"
3. Select task type (daily/weekly/all)

## Adding New Maps to Track

Edit `data/tracked_maps.json`:

```json
{
  "maps": [
    "8530-0110-2817",
    "0038-9297-7629",
    "NEW-MAP-CODE"
  ]
}
```

Maps in `data/raw/` are also automatically included.

## Data Storage Structure

```
data/
├── historical/
│   ├── 85300110281/           # Map code (no dashes)
│   │   ├── 2025-12-04.json
│   │   ├── 2025-12-05.json
│   │   └── ...
│   ├── 00389297629/
│   │   └── ...
│   └── _logs/
│       └── collection_2025-12-04.json
├── models/
│   ├── future_ccu_predictor.pkl
│   ├── future_ccu_metadata.json
│   ├── training_log.json
│   └── backups/
│       └── 20251204_120000/   # Backup before retrain
└── tracked_maps.json
```

## Benefits of Historical Data

With 30+ days of data, the anomaly detector can:
- ✅ Identify weekly patterns (weekends vs weekdays)
- ✅ Recognize holiday spikes as expected behavior
- ✅ Learn each map's "normal" behavior
- ✅ Distinguish true anomalies from recurring patterns
- ✅ Improve prediction accuracy over time

