import tkinter as tk
import json
import os
import logging

from utils import normalize_vidpid
from tkinter import messagebox, ttk

CONFIG_FILE = "config.json"
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

class ConfigGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("EnumGuardian 設定工具")
        self.config = self.load_config()
        self.build_widgets()
        
    def load_config(self):
        if not os.path.exists(CONFIG_FILE):
            return {
                "threshold": 100,
                "log_file": "enum_guardian_log.txt",
                "scan_strategy": {"mode": "scheduled", "time": "12:30", "days": [], "enabled": True},
                "monitored_devices": []
            }
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logging.error(f"[ConfigGUI] config.json 解析失敗：{e}")
            messagebox.showerror("錯誤", "config.json 格式錯誤，請修正或刪除重新建立")
            return {
                "threshold": 100,
                "log_file": "enum_guardian_log.txt",
                "scan_strategy": {"mode": "scheduled", "time": "12:30", "days": [], "enabled": True},
                "monitored_devices": []
            }

    def save_config(self): 
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)
        logging.info("[ConfigGUI] 設定已儲存至 config.json")
        messagebox.showinfo("完成", "設定已儲存！")

    def build_widgets(self):
        row = 0
        tk.Label(self.root, text="全域 ENUM 門檻").grid(row=row, column=0, sticky='e')
        self.threshold_var = tk.StringVar(value=str(self.config.get("threshold", 100)))
        tk.Entry(self.root, textvariable=self.threshold_var).grid(row=row, column=1, sticky='w')

        row += 1
        tk.Label(self.root, text="Log 檔案名稱").grid(row=row, column=0, sticky='e')
        self.log_file_var = tk.StringVar(value=self.config.get("log_file", "enum_guardian_log.txt"))
        tk.Entry(self.root, textvariable=self.log_file_var).grid(row=row, column=1, sticky='w')

        row += 1
        tk.Label(self.root, text="執行時間 (HH:MM)").grid(row=row, column=0, sticky='e')
        self.time_var = tk.StringVar(value=self.config.get("scan_strategy", {}).get("time", "12:30"))
        tk.Entry(self.root, textvariable=self.time_var).grid(row=row, column=1, sticky='w')

        row += 1
        self.enabled_var = tk.BooleanVar(value=self.config.get("scan_strategy", {}).get("enabled", True))
        tk.Checkbutton(self.root, text="啟用排程", variable=self.enabled_var).grid(row=row, column=1, sticky='w')

        row += 1
        tk.Label(self.root, text="週期選擇").grid(row=row, column=0, sticky='ne')
        self.day_vars = {}
        frame = tk.Frame(self.root)
        frame.grid(row=row, column=1, sticky='w')
        for day in WEEKDAYS:
            var = tk.BooleanVar(value=day in self.config.get("scan_strategy", {}).get("days", []))
            cb = tk.Checkbutton(frame, text=day, variable=var)
            cb.pack(side="left")
            self.day_vars[day] = var

        row += 1
        tk.Label(self.root, text="監控 VID:PID").grid(row=row, column=0, sticky='ne')
        self.vid_listbox = tk.Listbox(self.root, height=5, width=30, selectmode=tk.MULTIPLE)
        self.refresh_vid_list()
        self.vid_listbox.grid(row=row, column=1, sticky='w')

        row += 1
        self.new_vid_var = tk.StringVar()
        self.notify_threshold_var = tk.StringVar(value="50")
        frame_add = tk.Frame(self.root)
        frame_add.grid(row=row, column=1, sticky='w')
        tk.Label(frame_add, text="新增").pack(side='left')
        tk.Entry(frame_add, textvariable=self.new_vid_var, width=10).pack(side='left')
        tk.Label(frame_add, text="閾值").pack(side='left')
        tk.Entry(frame_add, textvariable=self.notify_threshold_var, width=5).pack(side='left')
        tk.Button(frame_add, text="新增裝置", command=self.add_vid).pack(side='left')

        row += 1
        tk.Button(self.root, text="刪除選取", command=self.remove_selected).grid(row=row, column=0)
        tk.Button(self.root, text="儲存設定", command=self.save).grid(row=row, column=1)

    def refresh_vid_list(self):
        self.vid_listbox.delete(0, tk.END)
        for item in self.config.get("monitored_devices", []):
            line = f'{normalize_vidpid(item["vid_pid"])} (閾值: {item.get("notify_threshold", "?")})'
            self.vid_listbox.insert(tk.END, line)

    def add_vid(self):
        vid = normalize_vidpid(self.new_vid_var.get())
        if not vid or len(vid) < 4:
            messagebox.showerror("錯誤", "請輸入合法的 VID:PID")
            return

        try:
            threshold = int(self.notify_threshold_var.get())
        except ValueError:
            messagebox.showerror("錯誤", "請輸入有效的閾值數字")
            return

        if all(normalize_vidpid(d["vid_pid"]) != vid for d in self.config["monitored_devices"]):
            self.config["monitored_devices"].append({"vid_pid": vid, "notify_threshold": threshold})
            self.refresh_vid_list()
            self.notify_threshold_var.set("50")
            self.save_config()
            logging.info(f"[ConfigGUI] 已新增監控裝置：{vid} 閾值={threshold}")
        else:
            messagebox.showwarning("警告", "裝置已存在或格式錯誤")
            logging.warning(f"[ConfigGUI] 嘗試加入重複裝置：{vid}")

    def remove_selected(self):
        if not self.vid_listbox.curselection():
            messagebox.showinfo("提示", "請先選取要刪除的項目")
            return

        selected = [normalize_vidpid(self.vid_listbox.get(i)) for i in self.vid_listbox.curselection()]
        self.config["monitored_devices"] = [
            d for d in self.config["monitored_devices"]
            if normalize_vidpid(d["vid_pid"]) not in selected
        ]
        self.refresh_vid_list()
        self.save_config()
        logging.info(f"[ConfigGUI] 刪除裝置：{selected}")

    def save(self):
        self.config["threshold"] = int(self.threshold_var.get())
        self.config["log_file"] = self.log_file_var.get()
        self.config["scan_strategy"] = {
            "enabled": self.enabled_var.get(),
            "time": self.time_var.get(),
            "days": [day for day, var in self.day_vars.items() if var.get()],
            "mode": "scheduled"
        }
        self.save_config()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
    root = tk.Tk()
    gui = ConfigGUI(root)
    gui.run()