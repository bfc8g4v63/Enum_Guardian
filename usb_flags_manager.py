import winreg
import ctypes

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
    
    if not auto:
        if not prompt_user_add_ignore_key(formatted_key):
            return False
    try:
        key_path = r"SYSTEM\\CurrentControlSet\\Control\\UsbFlags"
        with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path) as usb_flags:
            try:
                winreg.QueryValueEx(usb_flags, formatted_key)
                print(f"[UsbFlags] 已存在: {formatted_key}，略過設定")
                return True
            except FileNotFoundError:
                pass
            winreg.SetValueEx(usb_flags, formatted_key, 0, winreg.REG_BINARY, b'\x01')

        print(f"[UsbFlags] 已新增: {formatted_key}")
        return True
    except PermissionError:
        print("[UsbFlags] 權限不足，請以系統管理員身分執行")
    except Exception as e:
        print(f"[UsbFlags] 設定失敗: {e}")
    return False

if __name__ == "__main__":
    test_vidpid = "05A690B8"
    add_ignore_key_to_registry(test_vidpid)