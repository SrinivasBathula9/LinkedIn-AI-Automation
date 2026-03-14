"""
Region-timezone job definitions for the APScheduler.
Each region fires at 9:00 AM and 7:00 PM local time.
"""
import pytz

REGION_TIMEZONES: dict[str, str] = {
    "SG":  "Asia/Singapore",
    "IN":  "Asia/Kolkata",
    "UK":  "Europe/London",
    "EU":  "Europe/Berlin",
    "US":  "America/New_York",
    "UAE": "Asia/Dubai",
}

SCHEDULE_WINDOWS = [
    {"hour": 7, "minute": 15},    # 9:00 AM local
    {"hour": 19, "minute": 0}    # 7:00 PM local
]


def get_all_jobs() -> list[dict]:
    """Return list of job definitions with cron parameters."""
    jobs = []
    for region, tz_str in REGION_TIMEZONES.items():
        tz = pytz.timezone(tz_str)
        for window in SCHEDULE_WINDOWS:
            jobs.append({
                "id": f"campaign_{region}_{window['hour']}",
                "region": region,
                "timezone": tz,
                "hour": window["hour"],
                "minute": window["minute"],
            })
    return jobs
