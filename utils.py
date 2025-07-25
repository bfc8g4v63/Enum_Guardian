import logging

def normalize_vidpid(vidpid: str) -> str:
    if not isinstance(vidpid, str):
        logging.warning(f"[Utils] 警告：normalize_vidpid() 輸入類型非字串：{vidpid}")
        return ""

    return (
        vidpid.replace("VID_", "")
              .replace("PID_", "")
              .replace("&", "")
              .replace(":", "")
              .replace("_", "")
              .replace(" ", "")
              .strip()
              .upper()
    )