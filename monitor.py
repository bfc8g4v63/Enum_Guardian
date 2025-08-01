import winreg
import logging
from utils import normalize_vidpid
from utils import get_locked_list

def scan_all_vidpid_counts(threshold=50):
    counts = {}
    enum_path = r"SYSTEM\CurrentControlSet\Enum\USB"
    locked_list = get_locked_list("lock_list.json")

    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, enum_path) as usb_root:
            device_count = winreg.QueryInfoKey(usb_root)[0]
            for i in range(device_count):
                try:
                    subkey = winreg.EnumKey(usb_root, i)
                    norm_key = normalize_vidpid(subkey)

                    if norm_key in locked_list:
                        logging.info(f"[Monitor] 已鎖定 {norm_key}，略過統計")
                        continue

                    try:
                        with winreg.OpenKey(usb_root, subkey) as device_key:
                            instance_count = winreg.QueryInfoKey(device_key)[0]
                            if instance_count >= threshold:
                                counts[norm_key] = instance_count
                                logging.info(f"[Monitor] 偵測到 {norm_key} 子鍵數量 {instance_count}，超過門檻 {threshold}")
                            else:
                                logging.debug(f"[Monitor] {norm_key} 子鍵數 {instance_count} 未達門檻 {threshold}")
                    except PermissionError:
                        logging.warning(f"[Monitor] 權限不足，無法開啟裝置鍵: {subkey}")
                    except Exception as e:
                        logging.warning(f"[Monitor] 開啟子鍵失敗: {subkey} - {e}")
                except OSError:
                    continue
    except FileNotFoundError:
        logging.warning("[Monitor] 找不到 ENUM 註冊表路徑")
    except Exception as e:
        logging.error(f"[Monitor] 掃描全部裝置失敗: {e}")

    return counts