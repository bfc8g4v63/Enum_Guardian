import winreg
import ctypes
import logging
from utils import normalize_vidpid

IGNORE_SERIAL_NUM = b'\x01'

def format_ignore_key(vidpid: str) -> str:
    """將 VID/PID 轉為 Ignore 鍵名格式，會自動正規化"""
    vidpid = normalize_vidpid(vidpid)
    return f"IgnoreHWSerNum{vidpid}"

def prompt_user_add_ignore_key(formatted_key: str) -> bool:
    """跳出提示詢問是否加入 Ignore"""
    msg = f"是否將 {formatted_key} 加入 UsbFlags 中，以防止後續裝置增胖？"
    return ctypes.windll.user32.MessageBoxW(
        0, msg, "新增 Ignore 設定", 0x04 | 0x30
    ) == 6

def add_ignore_key_to_registry(vidpid: str, auto=True) -> bool:
    """將特定 VID/PID 加入 UsbFlags 註冊表 Ignore 項目"""
    formatted_key = format_ignore_key(vidpid)
    logging.debug(f"[UsbFlags] 準備設定 Ignore 鍵值: {formatted_key}")

    if not auto:
        if not prompt_user_add_ignore_key(formatted_key):
            return False

    try:
        key_path = r"SYSTEM\\CurrentControlSet\\Control\\UsbFlags"
        logging.debug(f"[UsbFlags] 嘗試開啟註冊表路徑: {key_path}")
        with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path) as usb_flags:
            try:
                winreg.QueryValueEx(usb_flags, formatted_key)
                logging.info(f"[UsbFlags] 已存在: {formatted_key}，略過設定")
                return True
            except FileNotFoundError:
                pass 

            logging.debug(f"[UsbFlags] 正在新增鍵值 {formatted_key} 至註冊表 {key_path}")
            winreg.SetValueEx(usb_flags, formatted_key, 0, winreg.REG_BINARY, IGNORE_SERIAL_NUM)
            logging.debug(f"[UsbFlags] 註冊表已寫入成功：{formatted_key}")

        logging.info(f"[UsbFlags] 已新增: {formatted_key}")
        return True

    except PermissionError:
        logging.warning("[UsbFlags] 權限不足，請以系統管理員或排程器方式執行")
    except Exception as e:
        logging.error(f"[UsbFlags] 設定 {formatted_key} 失敗: {e} (原始 vidpid={vidpid})")

    logging.debug(f"[UsbFlags] 設定 {formatted_key} 失敗")
    return False

def remove_ignore_key_from_registry(vidpid: str) -> bool:
    """從註冊表中移除指定 VID/PID 的 IgnoreHWSerNum 鍵"""
    formatted_key = format_ignore_key(vidpid)
    key_path = r"SYSTEM\\CurrentControlSet\\Control\\UsbFlags"

    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_ALL_ACCESS) as usb_flags:
            winreg.DeleteValue(usb_flags, formatted_key)
            logging.info(f"[UsbFlags] 已成功移除 Ignore 鍵：{formatted_key}")
            return True
    except FileNotFoundError:
        logging.warning(f"[UsbFlags] Ignore 鍵不存在：{formatted_key}")
        return False
    except PermissionError:
        logging.error(f"[UsbFlags] 權限不足，無法刪除：{formatted_key}")
    except Exception as e:
        logging.error(f"[UsbFlags] 刪除 Ignore 鍵失敗：{e}")

    return False

def list_all_ignore_keys() -> list:
    """列出所有目前 UsbFlags 中的 IgnoreHWSerNum 鍵"""
    key_path = r"SYSTEM\\CurrentControlSet\\Control\\UsbFlags"
    found_keys = []
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ) as key:
            i = 0
            while True:
                try:
                    name, _, _ = winreg.EnumValue(key, i)
                    if name.startswith("IgnoreHWSerNum"):
                        found_keys.append(name)
                    i += 1
                except OSError:
                    break
    except Exception as e:
        logging.error(f"[UsbFlags] 無法列出 UsbFlags 鍵：{e}")
    return found_keys

if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.DEBUG, format='[%(asctime)s] %(message)s')

    test_vidpid = "05A690B8"
    add_ignore_key_to_registry(test_vidpid, auto=False)
    remove_ignore_key_from_registry(test_vidpid)

    keys = list_all_ignore_keys()
    logging.info(f"[UsbFlags] 當前已設置 Ignore 清單共 {len(keys)} 項：{keys}")