import winreg
import subprocess
import json
import os
import logging

from utils import normalize_vidpid
LOCK_LIST_FILE = "lock_list.json"

def update_lock_list(lock_list_file: str, vidpid: str) -> bool:
    try:
        vidpid = normalize_vidpid(vidpid)
        if not os.path.exists(lock_list_file):
            data = {"locked": []}
        else:
            with open(lock_list_file, 'r') as f:
                data = json.load(f)

        if vidpid not in data.get("locked", []):
            data["locked"].append(vidpid)
            with open(lock_list_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            return True
        return False
    except Exception as e:
        logging.error(f"[Cleaner] 更新 Lock List 失敗: {e}")
        return False

def clean_comdb():
    comdb_path = r"SYSTEM\\CurrentControlSet\\Control\\COM Name Arbiter"
    try:

        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, comdb_path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, "ComDB", 0, winreg.REG_BINARY, b'\x00' * 128)
        print("[Cleaner] ComDB 位元已清空（128 bytes）")
    except PermissionError:
        print("[Cleaner] 權限不足，請使用系統管理員身分執行")
    except FileNotFoundError:
        print("[Cleaner] COMDB 註冊表不存在，可能尚未建立過裝置")
    except Exception as e:
        print(f"[Cleaner] 清除 ComDB 位元失敗: {e}")

def clean_enum_for_vidpid(vidpid: str):
    vidpid = normalize_vidpid(vidpid)
    base_key = r"SYSTEM\\CurrentControlSet\\Enum\\USB"
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base_key, 0, winreg.KEY_ALL_ACCESS) as root:
            i = 0
            to_delete = []
            while True:
                try:
                    subkey_name = winreg.EnumKey(root, i)
                    compare_key = normalize_vidpid(subkey_name)
                    if compare_key == vidpid:
                        to_delete.append(subkey_name)
                    i += 1
                except OSError:
                    break

            if not to_delete:
                print(f"[Cleaner] 找不到匹配 {vidpid} 的 VID/PID 項目，無項目可刪")

            for key in to_delete:
                try:
                    subprocess.run(f'reg delete "HKLM\\{base_key}\\{key}" /f', shell=True, check=True)
                    print(f"[Cleaner] 已刪除 ENUM 註冊表項目: {key}")
                except subprocess.CalledProcessError as e:
                    print(f"[Cleaner] 刪除 {key} 發生錯誤: {e}")
    except PermissionError:
        print("[Cleaner] 權限不足，請使用系統管理員身分執行")
    except Exception as e:
        print(f"[Cleaner] 清除 ENUM 失敗: {e}")
