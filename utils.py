def normalize_vidpid(vidpid: str) -> str:
    return (
        vidpid.replace("VID_", "")
              .replace("PID_", "")
              .replace("&", "")
              .replace(":", "")
              .replace("_", "")
              .strip()
              .upper()
    )
