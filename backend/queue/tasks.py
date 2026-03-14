"""
Celery async task definitions.
Wraps async automation functions for Celery compatibility.
"""
import asyncio
from backend.queue.celery_app import celery_app


@celery_app.task(name="backend.queue.tasks.run_campaign_task", bind=True, max_retries=3)
def run_campaign_task(self, campaign_id: str, region: str) -> dict:
    """Celery task: run a connection campaign for a region."""
    from backend.automation.browser_agent import run_connection_campaign
    try:
        asyncio.run(run_connection_campaign(campaign_id=campaign_id, region=region))
        return {"status": "success", "campaign_id": campaign_id, "region": region}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@celery_app.task(name="backend.queue.tasks.classify_profile_task")
def classify_profile_task(profile: dict) -> dict:
    """Celery task: classify a single profile and return result."""
    from backend.ai.classifier import classifier
    from backend.ai.scorer import compute_relevance_score

    cls = classifier.predict(profile)
    score = compute_relevance_score(profile)
    return {
        "is_relevant": cls["is_relevant"],
        "confidence": cls["confidence"],
        "relevance_score": score,
    }
