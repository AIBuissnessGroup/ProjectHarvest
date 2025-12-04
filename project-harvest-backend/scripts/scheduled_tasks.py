"""
Scheduled Tasks Runner
=======================
A unified script to run scheduled tasks.
Can be triggered by cron, Railway, or GitHub Actions.

Usage:
    python scripts/scheduled_tasks.py daily    # Run daily tasks
    python scripts/scheduled_tasks.py weekly   # Run weekly tasks
    python scripts/scheduled_tasks.py all      # Run all tasks
"""

import sys
import asyncio
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def run_daily_tasks():
    """
    Daily tasks:
    1. Collect CCU data for all tracked maps
    """
    print("=" * 60)
    print(f"📅 DAILY TASKS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Task 1: Collect daily CCU data
    print("\n📊 Task 1: Collecting daily CCU data...")
    from scripts.collect_daily_ccu import collect_daily_data
    
    results = asyncio.run(collect_daily_data())
    
    print(f"\n✅ Daily collection complete:")
    print(f"   Successful: {results['successful']}")
    print(f"   Skipped: {results['skipped']}")
    print(f"   Failed: {results['failed']}")
    
    return results


def run_weekly_tasks():
    """
    Weekly tasks:
    1. Auto-retrain models if enough new data
    """
    print("=" * 60)
    print(f"📅 WEEKLY TASKS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Task 1: Auto-retrain models
    print("\n🤖 Task 1: Checking if model retraining needed...")
    from scripts.auto_retrain import auto_retrain
    
    results = auto_retrain(force=False, dry_run=False)
    
    print(f"\n✅ Retraining check complete:")
    print(f"   Action: {results['action']}")
    print(f"   Reason: {results.get('reason', 'N/A')}")
    
    return results


def run_all_tasks():
    """Run all scheduled tasks."""
    print("🚀 Running ALL scheduled tasks...\n")
    
    daily_results = run_daily_tasks()
    print("\n" + "-" * 60 + "\n")
    weekly_results = run_weekly_tasks()
    
    return {
        "daily": daily_results,
        "weekly": weekly_results
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/scheduled_tasks.py [daily|weekly|all]")
        sys.exit(1)
    
    task_type = sys.argv[1].lower()
    
    if task_type == "daily":
        run_daily_tasks()
    elif task_type == "weekly":
        run_weekly_tasks()
    elif task_type == "all":
        run_all_tasks()
    else:
        print(f"Unknown task type: {task_type}")
        print("Valid options: daily, weekly, all")
        sys.exit(1)


if __name__ == "__main__":
    main()

