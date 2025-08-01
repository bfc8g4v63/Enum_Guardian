import json
import logging
import os
import re
import sys
from datetime import datetime
from utils import normalize_vidpid, get_locked_list
from monitor import scan_all_vidpid_counts
from cleaner import clean_enum_for_vidpid, clean_comdb
from usb_flags_manager import add_ignore_key_to_registry
from scheduler import should_execute_now

if getattr(sys, 'frozen', False):
    os.chdir(os.path.dirname(sys.executable))
else:
    os.chdir(os.path.dirname(__file__))

CONFIG_FILE = "config.json"
LOCK_FILE = "last_comdb_cleaned.log"
FAILED_DIR = "failed_logs"

with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
    config = json.load(f)

for dev in config.get("monitored_devices", []):
    original = dev.get("vid_pid", "")
    cleaned = re.sub(r"&MI_[0-9A-Fa-f]{2}", "", original)
    if original != cleaned:
        logging.debug(f"[AUTO] 清理 config VIDPID: {original} → {cleaned}")
        dev["vid_pid"] = cleaned

LOG_FILE = config.get("log_file", "enum_guardian_log.txt")

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

AUTO_THRESHOLD = config.get("threshold", 100)

def should_clean_comdb_today():
    today = datetime.now().strftime("%Y-%m-%d")
    if not os.path.exists(LOCK_FILE):
        return True
    with open(LOCK_FILE, "r", encoding='utf-8') as f:
        last = f.read().strip()
    return last != today

def mark_comdb_cleaned():
    today = datetime.now().strftime("%Y-%m-%d")
    with open(LOCK_FILE, "w", encoding='utf-8') as f:
        f.write(today)

def main():
    logging.info("[AUTO] ====== EnumGuardian Auto Scan & Cleanup Started ======")

    scan_strategy = config.get("scan_strategy", {})
    if not should_execute_now(scan_strategy):
        logging.info("[AUTO] 當前不在設定執行時間，已退出。")
        return

    failed = []
    locked_list = get_locked_list()

    try:
        counts = scan_all_vidpid_counts(threshold=AUTO_THRESHOLD)
    except Exception as e:
        logging.error(f"[AUTO] 裝置掃描失敗：{e}")
        return

    logging.info(f"[AUTO] 本次掃描共偵測到 {len(counts)} 個裝置項目")
    sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)

    monitored_dict = {
        normalize_vidpid(d["vid_pid"]): d.get("notify_threshold", 50)
        for d in config.get("monitored_devices", [])
    }

    cleaned_count = 0
    skipped_count = 0

    for idx, (vidpid_raw, count) in enumerate(sorted_counts, start=1):
        vidpid = normalize_vidpid(vidpid_raw)

        if vidpid in locked_list:
            logging.info(f"[AUTO] [{idx}] {vidpid} 已存在於 Lock List，跳過")
            skipped_count += 1
            continue

        try:
            if vidpid not in monitored_dict:
                logging.info(f"[AUTO] [{idx}] {vidpid} 未在監控清單，將新增")
                config["monitored_devices"].append({"vid_pid": vidpid, "notify_threshold": 50})
                monitored_dict[vidpid] = 50

            add_ignore_key_to_registry(vidpid, auto=True)
            clean_enum_for_vidpid(vidpid)
            cleaned_count += 1
        except Exception as e:
            logging.error(f"[AUTO] [{idx}] 清理 {vidpid} 發生錯誤：{e}")
            failed.append({"vid_pid": vidpid, "count": count, "error": str(e)})

    logging.info("[AUTO] 第二次掃描確認中...")
    try:
        counts_2 = scan_all_vidpid_counts(threshold=AUTO_THRESHOLD)
    except Exception as e:
        logging.error(f"[AUTO] 第二次掃描失敗：{e}")
        return

    sorted_counts_2 = sorted(counts_2.items(), key=lambda x: x[1], reverse=True)
    has_second_clean = False

    for idx, (vidpid_raw, count) in enumerate(sorted_counts_2, start=1):
        vidpid = normalize_vidpid(vidpid_raw)

        if vidpid in locked_list:
            continue

        try:
            if vidpid not in monitored_dict:
                config["monitored_devices"].append({"vid_pid": vidpid, "notify_threshold": 50})
                monitored_dict[vidpid] = 50

            add_ignore_key_to_registry(vidpid, auto=True)
            clean_enum_for_vidpid(vidpid)
            has_second_clean = True
            cleaned_count += 1
        except Exception as e:
            failed.append({"vid_pid": vidpid, "count": count, "error": str(e)})

    if has_second_clean:
        logging.info("[AUTO] 第二次補清完成。")
    elif sorted_counts_2:
        logging.warning("[AUTO] 第二次掃描仍有未清除裝置，建議人工確認")

    if should_clean_comdb_today():
        try:
            clean_comdb()
            mark_comdb_cleaned()
            logging.info("[AUTO] 今日COMDB清理完成")
        except Exception as e:
            logging.error(f"[AUTO] COMDB清理失敗：{e}")

    if failed:
        today_str = datetime.now().strftime("%Y-%m-%d")
        os.makedirs(FAILED_DIR, exist_ok=True)
        failed_filename = os.path.join(FAILED_DIR, f"failed_{today_str}.json")

        for item in failed:
            item["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            with open(failed_filename, 'w', encoding='utf-8') as f:
                json.dump(failed, f, indent=4, ensure_ascii=False)
            logging.warning(f"[AUTO] 共 {len(failed)} 項清理失敗，已儲存至：{failed_filename}")
        except Exception as e:
            logging.error(f"[AUTO] 儲存失敗清單錯誤：{e}")

    logging.info(f"[AUTO] 本次清理完成，共處理 {cleaned_count} 項，跳過 {skipped_count} 項")
    logging.info("[AUTO] ====== 全部流程執行完畢 ======")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        logging.error(f"未捕捉的錯誤：{e}")
        with open("fatal_error.log", "w", encoding="utf-8") as f:
            f.write(traceback.format_exc())
        logging.error(traceback.format_exc())
        print("發生重大錯誤，請查看 fatal_error.log")