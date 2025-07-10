import winreg

from utils import normalize_vidpid

def scan_enum_count(target_vidpid):
    count = 0
    enum_path = r"SYSTEM\CurrentControlSet\Enum\USB"
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, enum_path) as usb_root:
            norm_target = normalize_vidpid(target_vidpid)
            for i in range(winreg.QueryInfoKey(usb_root)[0]):
                subkey_name = winreg.EnumKey(usb_root, i)
                norm_sub = normalize_vidpid(subkey_name)
                if norm_sub == norm_target:
                    try:
                        with winreg.OpenKey(usb_root, subkey_name) as device_key:
                            for j in range(winreg.QueryInfoKey(device_key)[0]):
                                try:
                                    _ = winreg.EnumKey(device_key, j)
                                    count += 1
                                except OSError:
                                    continue
                    except Exception as e:
                        print(f"[Monitor] Failed to open subkey {subkey_name}: {e}")
    except Exception as e:
        print(f"[Monitor] Error scanning registry: {e}")
    return count

def scan_all_vidpid_counts():
    counts = {}
    enum_path = r"SYSTEM\CurrentControlSet\Enum\USB"
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, enum_path) as usb_root:
            for i in range(winreg.QueryInfoKey(usb_root)[0]):
                try:
                    subkey_name = winreg.EnumKey(usb_root, i)
                    norm = normalize_vidpid(subkey_name)
                    with winreg.OpenKey(usb_root, subkey_name) as device_key:
                        instance_count = 0
                        for j in range(winreg.QueryInfoKey(device_key)[0]):
                            try:
                                _ = winreg.EnumKey(device_key, j)
                                instance_count += 1
                            except OSError:
                                continue
                        counts[norm] = instance_count
                except FileNotFoundError:
                    continue
                except OSError as oe:
                    print(f"[Monitor] Skip invalid subkey: {oe}")
                    continue
    except Exception as e:
        print(f"[Monitor] Error scanning all VID/PID: {e}")
    return counts