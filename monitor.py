import winreg
import logging
from utils import normalize_vidpid

def get_instance_count(device_key):
    count = 0
    for j in range(winreg.QueryInfoKey(device_key)[0]):
        try:
            _ = winreg.EnumKey(device_key, j)
            count += 1
        except OSError:
            continue
    return count

def scan_enum_count(target_vidpid):
    count = 0
    enum_path = r"SYSTEM\CurrentControlSet\Enum\USB"
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, enum_path) as usb_root:
            norm_target = normalize_vidpid(target_vidpid)
            for i in range(winreg.QueryInfoKey(usb_root)[0]):
                try:
                    parent_key = winreg.EnumKey(usb_root, i)
                    parent_norm = normalize_vidpid(parent_key)

                    if norm_target in parent_norm:
                        with winreg.OpenKey(usb_root, parent_key) as device_key:
                            for j in range(winreg.QueryInfoKey(device_key)[0]):
                                try:
                                    subkey = winreg.EnumKey(device_key, j)
                                    full_key = f"{parent_key}\\{subkey}"
                                    with winreg.OpenKey(device_key, subkey) as sub_dev:
                                        instance_count = get_instance_count(sub_dev)
                                        count += instance_count
                                except Exception as e:
                                    logging.warning(f"[Monitor] 子鍵錯誤 {subkey}: {e}")

                except Exception as e:
                    logging.warning(f"[Monitor] 主鍵錯誤 {e}")
    except Exception as e:
        logging.error(f"[Monitor] Registry 掃描錯誤: {e}")

    logging.info(f"[Monitor] 完成掃描 {target_vidpid}：共 {count} 個實例（含子鍵）")
    return count

def scan_all_vidpid_counts():
    counts = {}
    enum_path = r"SYSTEM\CurrentControlSet\Enum\USB"
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, enum_path) as usb_root:
            for i in range(winreg.QueryInfoKey(usb_root)[0]):
                try:
                    parent_key = winreg.EnumKey(usb_root, i)
                    with winreg.OpenKey(usb_root, parent_key) as device_key:
                        for j in range(winreg.QueryInfoKey(device_key)[0]):
                            try:
                                subkey = winreg.EnumKey(device_key, j)
                                full_key = f"{parent_key}&{subkey}"
                                norm_full = normalize_vidpid(full_key)
                                with winreg.OpenKey(device_key, subkey) as sub_dev:
                                    count = get_instance_count(sub_dev)
                                    counts[norm_full] = count
                            except Exception as e:
                                logging.warning(f"[Monitor] 無法開啟子鍵 {subkey}: {e}")
                except OSError:
                    continue
    except Exception as e:
        logging.error(f"[Monitor] Error scanning all VID/PID: {e}")

    logging.info(f"[Monitor] 全部 VID/PID（含子鍵）掃描完成，共 {len(counts)} 項")
    return counts