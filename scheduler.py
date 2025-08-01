import datetime
import logging

WEEKDAYS_MAP = {
    "Mon": 0,
    "Tue": 1,
    "Wed": 2,
    "Thu": 3,
    "Fri": 4,
    "Sat": 5,
    "Sun": 6
}

TIME_TOLERANCE_SECONDS = 300

def should_run_today(scan_strategy):
    """檢查今日是否為排程允許執行的星期幾"""
    logging.debug(f"[Scheduler] 執行週期策略檢查: {scan_strategy}")

    if not scan_strategy.get("enabled", False):
        return False

    mode = scan_strategy.get("mode", "manual")

    if mode not in ("manual", "daily", "weekly", "scheduled"):
        logging.warning(f"[Scheduler] 不支援的模式: {mode}")
        return False

    if mode == "manual":
        return False
    if mode == "daily":
        return True

    if mode in ("weekly", "scheduled"):
        weekdays = scan_strategy.get("days", [])
        today = datetime.datetime.today().weekday()
        weekday_indexes = []
        for day in weekdays:
            index = WEEKDAYS_MAP.get(day.capitalize(), -1)
            if index == -1:
                logging.warning(f"[Scheduler] 無效的星期縮寫: {day}")
            else:
                weekday_indexes.append(index)
        return today in weekday_indexes

    return False

def is_time_to_run(scan_strategy):
    now = datetime.datetime.now()
    target_time_str = scan_strategy.get("time", "00:00")
    try:
        target_time = datetime.datetime.strptime(target_time_str, "%H:%M")
    except ValueError:
        example_time = now.strftime("%H:%M")
        logging.warning(f"[Scheduler] 時間格式錯誤（應為 HH:MM，如 08:30）。收到：{target_time_str}，目前時間範例：{example_time}")
        return False

    scheduled_time = now.replace(hour=target_time.hour, minute=target_time.minute, second=0, microsecond=0)
    delta = abs((now - scheduled_time).total_seconds())
    tolerance = scan_strategy.get("tolerance", TIME_TOLERANCE_SECONDS)

    if delta <= tolerance:
        logging.debug(f"[Scheduler] 現在時間 {now.strftime('%H:%M:%S')} 接近排程時間 {target_time_str}")
        return True
    else:
        logging.debug(f"[Scheduler] 距排程時間超過 {tolerance} 秒，略過執行")
        return False

def should_execute_now(scan_strategy):
    today_check = should_run_today(scan_strategy)
    time_check = is_time_to_run(scan_strategy)
    logging.info(f"[Scheduler] Date Check: {today_check}, Time Check: {time_check}")

    if not today_check:
        logging.info("[Scheduler] 今日不在排程日期，跳過執行")
    elif not time_check:
        logging.info("[Scheduler] 時間尚未到排程指定時間，跳過執行")
    else:
        logging.info("[Scheduler] 符合排程條件，執行開始")

    return today_check and time_check