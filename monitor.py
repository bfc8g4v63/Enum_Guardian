import winreg

def normalize_vidpid(vidpid):
    return (
        vidpid.upper()
        .replace("VID_", "")
        .replace("PID_", "")
        .replace("&", "")
        .replace("_", "")
        .strip()
    )

def scan_enum_count(target_vidpid):
    count = 0
    try:
        enum_path = r"SYSTEM\\CurrentControlSet\\Enum\\USB"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, enum_path) as usb_root:
            for i in range(winreg.QueryInfoKey(usb_root)[0]):
                subkey_name = winreg.EnumKey(usb_root, i)
                norm_sub = normalize_vidpid(subkey_name)
                norm_target = normalize_vidpid(target_vidpid)
                if norm_sub.startswith(norm_target):
                    count += 1
    except Exception as e:
        print(f"[Monitor] Error scanning registry: {e}")
    return count

def scan_all_vidpid_counts():
    counts = {}
    try:
        enum_path = r"SYSTEM\\CurrentControlSet\\Enum\\USB"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, enum_path) as usb_root:
            for i in range(winreg.QueryInfoKey(usb_root)[0]):
                subkey_name = winreg.EnumKey(usb_root, i)
                norm = normalize_vidpid(subkey_name)
                counts[norm] = counts.get(norm, 0) + 1
    except Exception as e:
        print(f"[Monitor] Error scanning all VID/PID: {e}")
    return counts