"""APScheduler bootstrap and re-analysis job runner."""
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

_scheduler = None


def get_scheduler():
    return _scheduler


def init_scheduler(app):
    global _scheduler
    if _scheduler is not None:
        return _scheduler
    _scheduler = BackgroundScheduler(daemon=True, timezone="UTC")
    _scheduler.start()
    app._scheduler = _scheduler

    def _bootstrap():
        with app.app_context():
            try:
                from app.models import ScheduledJob
                jobs = ScheduledJob.query.filter_by(is_enabled=True).all()
                for job in jobs:
                    register_job(app, job)
            except Exception as exc:
                app.logger.warning("Scheduler bootstrap deferred: %s", exc)

    try:
        _bootstrap()
    except Exception:
        pass

    return _scheduler


def _job_id(store_id):
    return f"store_reanalysis_{store_id}"


def register_job(app, scheduled_job):
    if not _scheduler:
        return
    try:
        trigger = CronTrigger.from_crontab(scheduled_job.cron_expression)
    except Exception as exc:
        app.logger.warning("Invalid cron for store %s: %s", scheduled_job.store_id, exc)
        return
    _scheduler.add_job(
        run_reanalysis,
        trigger=trigger,
        args=[app, scheduled_job.store_id],
        id=_job_id(scheduled_job.store_id),
        replace_existing=True,
    )


def unregister_job(store_id):
    if not _scheduler:
        return
    try:
        _scheduler.remove_job(_job_id(store_id))
    except Exception:
        pass


def run_reanalysis(app, store_id):
    with app.app_context():
        from extensions import db
        from app.models import Store, ScheduledJob, User, UserRole
        from app.services import dataset_service
        from app.services.audit_service import log_event
        from app.services.email_service import send_scheduled_summary_email

        store = db.session.get(Store, store_id)
        job = ScheduledJob.query.filter_by(store_id=store_id).first()
        if not store or not job:
            return
        job.last_run_status = "running"
        db.session.commit()
        try:
            df, dataset = dataset_service.get_active_dataframe(store)
            if df is None:
                raise RuntimeError("Store has no active dataset")
            from app.services import analytics_service, mba_service
            summary = analytics_service.compute_summary(df)
            rules = mba_service.compute_association_rules(df, limit=10)
            payload = {"summary": summary, "rules": rules, "generated_at": datetime.utcnow().isoformat()}

            manager = User.query.filter_by(store_id=store.id, role=UserRole.STORE_MANAGER).first()
            recipient_email = job.email_summary_to or (manager.email if manager else None)
            if manager and recipient_email:
                manager.email = recipient_email
                send_scheduled_summary_email(manager, store, payload)
            job.last_run_status = "success"
            job.last_run_error = None
            log_event("scheduled_job_run", target_type="store", target_id=store.id, metadata={"status": "success"})
        except Exception as exc:
            app.logger.exception("Scheduled re-analysis failed for store %s", store_id)
            job.last_run_status = "failed"
            job.last_run_error = str(exc)
            log_event("scheduled_job_run", target_type="store", target_id=store.id, metadata={"status": "failed", "error": str(exc)})
        finally:
            job.last_run_at = datetime.utcnow()
            db.session.commit()
