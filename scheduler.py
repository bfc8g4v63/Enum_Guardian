import datetime
import time

WEEKDAYS_MAP = {
    "Mon": 0,
    "Tue": 1,
    "Wed": 2,
    "Thu": 3,
    "Fri": 4,
    "Sat": 5,
    "Sun": 6
}

def should_run_today(scan_strategy):
    if not scan_strategy.get("enabled", False):
        return False

    mode = scan_strategy.get("mode", "manual")
    if mode == "manual":
        return False
    if mode == "daily":
        return True

    if mode in ("weekly", "scheduled"):
        weekdays = scan_strategy.get("days", [])
        today = datetime.datetime.today().weekday()
        weekday_indexes = [WEEKDAYS_MAP.get(day, -1) for day in weekdays]
        return today in weekday_indexes

    return False

def is_time_to_run(scan_strategy):
    now = datetime.datetime.now()
    target_time_str = scan_strategy.get("time", "00:00")

    try:
        target_time = datetime.datetime.strptime(target_time_str, "%H:%M")
    except ValueError:
        print(f"[Scheduler] 時間格式錯誤（應為 HH:MM）: {target_time_str}")
        return False

    diff = abs((now - now.replace(hour=target_time.hour, minute=target_time.minute, second=0, microsecond=0)).total_seconds())
    return diff <= 300

def should_execute_now(scan_strategy):
    today_check = should_run_today(scan_strategy)
    time_check = is_time_to_run(scan_strategy)
    print(f"[Scheduler] Date Check: {today_check}, Time Check: {time_check}")
    return today_check and time_check
