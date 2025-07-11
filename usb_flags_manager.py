import winreg
import ctypes
import logging
from utils import normalize_vidpid

def format_ignore_key(vidpid: str) -> str:
    vidpid = normalize_vidpid(vidpid)
    return f"IgnoreHWSerNum{vidpid}"

def prompt_user_add_ignore_key(formatted_key: str) -> bool:
    msg = f"是否將 {formatted_key} 加入 UsbFlags 中，以防止後續裝置增胖？"
    return ctypes.windll.user32.MessageBoxW(
        0, msg, "新增 Ignore 設定", 0x04 | 0x30
    ) == 6

def add_ignore_key_to_registry(vidpid: str, auto=True) -> bool:
    formatted_key = format_ignore_key(vidpid)
    logging.debug(f"[UsbFlags] 準備設定 Ignore 鍵值: {formatted_key}")

    if not auto:
        if not prompt_user_add_ignore_key(formatted_key):
            return False
    try:
        key_path = r"SYSTEM\\CurrentControlSet\\Control\\UsbFlags"
        with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path) as usb_flags:
            try:
                winreg.QueryValueEx(usb_flags, formatted_key)
                logging.info(f"[UsbFlags] 已存在: {formatted_key}，略過設定")
                return True
            except FileNotFoundError:
                pass

            logging.debug(f"[UsbFlags] 正在新增鍵值 {formatted_key} 至註冊表 {key_path}")
            winreg.SetValueEx(usb_flags, formatted_key, 0, winreg.REG_BINARY, b'\x01')

        logging.info(f"[UsbFlags] 已新增: {formatted_key}")
        return True
    except PermissionError:
        logging.warning("[UsbFlags] 權限不足，請以系統管理員身分執行")
    except Exception as e:
        logging.error(f"[UsbFlags] 設定失敗: {e}")

    logging.debug(f"[UsbFlags] 設定 {formatted_key} 失敗")
    return False

if __name__ == "__main__":
    test_vidpid = "05A690B8"
    add_ignore_key_to_registry(test_vidpid)