"""
services/spotify_scheduler.py — APScheduler background sync service.

Runs sync_user_recent_plays() for every user who has sync_enabled=True,
every 30 minutes, as a background thread started at FastAPI lifespan startup.
"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from database import SessionLocal, SpotifyUser
from services.spotify_sync import sync_user_recent_plays

logger = logging.getLogger("spotify_scheduler")

_scheduler: BackgroundScheduler | None = None


def _run_sync_for_all_enabled_users() -> None:
    """Fetch all sync_enabled users and run sync for each one."""
    db = SessionLocal()
    try:
        users = db.query(SpotifyUser).filter(SpotifyUser.sync_enabled == True).all()
        user_ids = [u.user_id for u in users]
    except Exception as e:
        logger.error(f"[spotify_scheduler] Failed to query sync_enabled users: {e}")
        return
    finally:
        db.close()

    if not user_ids:
        return

    logger.info(f"[spotify_scheduler] Syncing {len(user_ids)} user(s)")
    for uid in user_ids:
        try:
            result = sync_user_recent_plays(uid)
            logger.info(f"[spotify_scheduler] user={uid} → {result}")
        except Exception as e:
            logger.error(f"[spotify_scheduler] user={uid} error: {e}")


def start_scheduler() -> None:
    """Start the background scheduler. Safe to call multiple times (idempotent)."""
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        return

    _scheduler = BackgroundScheduler(daemon=True)
    _scheduler.add_job(
        _run_sync_for_all_enabled_users,
        trigger=IntervalTrigger(minutes=30),
        id="spotify_sync_all",
        name="Spotify recent-plays sync (all enabled users)",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=60,
    )
    _scheduler.start()
    logger.info("[spotify_scheduler] Scheduler started — syncing every 30 minutes")


def stop_scheduler() -> None:
    """Gracefully stop the scheduler on app shutdown."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("[spotify_scheduler] Scheduler stopped")
