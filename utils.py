import os
import json
import logging

def normalize_vidpid(vidpid: str) -> str:
    """標準化 VID/PID 字串格式（去除前綴與符號後轉大寫）"""
    if not isinstance(vidpid, str):
        logging.warning(f"[Utils] 警告：normalize_vidpid() 輸入類型非字串：{vidpid}")
        return ""

    vidpid = vidpid.strip().upper()
    normalized = (
        vidpid.replace("VID_", "")
              .replace("PID_", "")
              .replace("&", "")
              .replace(":", "")
              .replace("_", "")
              .replace(" ", "")
    )

    if len(normalized) != 8:
        logging.warning(f"[Utils] normalize_vidpid() 結果長度異常：{normalized}")
    return normalized

def get_locked_list(lock_list_file: str = "lock_list.json") -> list[str]:
    """讀取鎖定的 VIDPID 清單，預期格式：{"locked": [ "VIDXXXXPIDYYYY", ... ]}"""
    try:
        if not os.path.exists(lock_list_file):
            return []
        with open(lock_list_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        locked = data.get("locked", [])
        if not isinstance(locked, list):
            logging.error(f"[Utils] lock_list.json 格式錯誤，locked 應為 list：{type(locked)}")
            return []
        if not all(isinstance(item, str) for item in locked):
            logging.error(f"[Utils] locked 清單內容非全為字串：{locked}")
            return []
        return locked
    except Exception as e:
        logging.error(f"[Utils] 載入 Lock List 失敗：{e}")
        return []