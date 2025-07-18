import json
import logging
import os
import sys
from datetime import datetime
from utils import normalize_vidpid
from monitor import scan_all_vidpid_counts, get_instance_count
from cleaner import clean_enum_for_vidpid, clean_comdb
from usb_flags_manager import add_ignore_key_to_registry
from scheduler import should_execute_now

if getattr(sys, 'frozen', False):
    os.chdir(os.path.dirname(sys.executable))
else:
    os.chdir(os.path.dirname(__file__))

CONFIG_FILE = "config.json"
LOCK_FILE = "last_comdb_cleaned.log"
FAILED_FILE = "failed_cleanup.json"

with open(CONFIG_FILE, 'r') as f:
    config = json.load(f)

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
    with open(LOCK_FILE, "r") as f:
        last = f.read().strip()
    return last != today

def mark_comdb_cleaned():
    today = datetime.now().strftime("%Y-%m-%d")
    with open(LOCK_FILE, "w") as f:
        f.write(today)

def main():
    logging.info("[AUTO] ====== EnumGuardian Auto Scan & Cleanup Started ======")

    scan_strategy = config.get("scan_strategy", {})
    if not should_execute_now(scan_strategy):
        logging.info("[AUTO] 當前不在設定執行時間，已退出。")
        return

    failed = []

    try:
        counts = scan_all_vidpid_counts()
    except Exception as e:
        logging.error(f"[AUTO] 裝置掃描失敗：{e}")
        return

    logging.info(f"[AUTO] 本次掃描共偵測到 {len(counts)} 個裝置項目")
    sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    logging.info("[AUTO] 初次掃描結果（依數量排序）:")
    for idx, (vidpid_raw, count) in enumerate(sorted_counts, start=1):
        logging.info(f"    [{idx}] {vidpid_raw} Count: {count}")

    for idx, (vidpid_raw, count) in enumerate(sorted_counts, start=1):
        vidpid = normalize_vidpid(vidpid_raw)

        monitored_dict = {
            normalize_vidpid(d["vid_pid"]): d.get("notify_threshold", 50)
            for d in config.get("monitored_devices", [])
        }

        try:
            if vidpid in monitored_dict:
                threshold = monitored_dict[vidpid]
                if count > threshold:
                    logging.info(f"[AUTO] [{idx}] {vidpid} 超過門檻 ({count}>{threshold}) 開始處理")
                    add_ignore_key_to_registry(vidpid, auto=True)
                    clean_enum_for_vidpid(vidpid)
            elif count >= AUTO_THRESHOLD:
                logging.info(f"[AUTO] [{idx}] {vidpid} 未監控但超過全域門檻 ({count}>={AUTO_THRESHOLD})，檢查是否已存在清單")
                already_monitored = any(normalize_vidpid(d["vid_pid"]) == vidpid for d in config["monitored_devices"])
                if not already_monitored:
                    config["monitored_devices"].append({"vid_pid": vidpid, "notify_threshold": 50})
                    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                        json.dump(config, f, indent=4, ensure_ascii=False)
                    logging.info(f"[AUTO] [{idx}] 已新增 {vidpid} 到監控清單")
                    logging.info(f"[AUTO] 目前監控清單總數：{len(config['monitored_devices'])}")
                else:
                    logging.info(f"[AUTO] [{idx}] {vidpid} 已在監控清單中，跳過新增")

                add_ignore_key_to_registry(vidpid, auto=True)
                clean_enum_for_vidpid(vidpid)

        except Exception as e:
            logging.error(f"[AUTO] [{idx}] 清理 {vidpid} 發生錯誤：{e}")
            failed.append({"vid_pid": vidpid, "count": count, "error": str(e)})

    logging.info("[AUTO] 第二次掃描確認中...")
    try:
        counts_2 = scan_all_vidpid_counts()
    except Exception as e:
        logging.error(f"[AUTO] 第二次掃描失敗：{e}")
        return

    sorted_counts_2 = sorted(counts_2.items(), key=lambda x: x[1], reverse=True)
    has_second_clean = False

    monitored_dict = {
        normalize_vidpid(d["vid_pid"]): d.get("notify_threshold", 50)
        for d in config.get("monitored_devices", [])
    }

    for idx, (vidpid_raw, count) in enumerate(sorted_counts_2, start=1):
        vidpid = normalize_vidpid(vidpid_raw)

        try:
            if vidpid in monitored_dict and count > monitored_dict[vidpid]:
                logging.info(f"[AUTO] 第二次清理 {vidpid} Count: {count}")
                add_ignore_key_to_registry(vidpid, auto=True)
                clean_enum_for_vidpid(vidpid)
                has_second_clean = True
            elif vidpid not in monitored_dict and count >= AUTO_THRESHOLD:
                logging.info(f"[AUTO] 第二次清理新裝置 {vidpid} Count: {count}")
                config["monitored_devices"].append({"vid_pid": vidpid, "notify_threshold": 50})
                with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=4, ensure_ascii=False)
                add_ignore_key_to_registry(vidpid, auto=True)
                clean_enum_for_vidpid(vidpid)
                has_second_clean = True
        except Exception as e:
            logging.error(f"[AUTO] 第二次清理 {vidpid} 失敗：{e}")
            failed.append({"vid_pid": vidpid, "count": count, "error": str(e)})

    if not has_second_clean:
        logging.info("[AUTO] 第二次掃描無需清理。")

    if should_clean_comdb_today():
        try:
            clean_comdb()
            mark_comdb_cleaned()
            logging.info("[AUTO] 今日COMDB清理完成")
        except Exception as e:
            logging.error(f"[AUTO] COMDB清理失敗：{e}")

    with open(FAILED_FILE, 'w', encoding='utf-8') as f:
        json.dump(failed, f, indent=4, ensure_ascii=False)

    if failed:
        logging.warning(f"[AUTO] 共 {len(failed)} 項清理失敗")
        for i, item in enumerate(failed, start=1):
            logging.warning(f"[AUTO] [{i}] {item['vid_pid']} ({item['count']}): {item['error']}")

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