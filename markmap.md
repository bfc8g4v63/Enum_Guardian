# EnumGuardian 系統

## 排程執行
- Windows 排程器每日 00:10 啟動 enum_auto_run
- 支援 ±5分鐘容差

## 掃描邏輯
- 掃描所有 Enum VID:PID
- 計算每個數量
- 排序結果 (多到少)

## 監控判斷
- 如果在 monitored_devices:
  - 比對 notify_threshold
  - 超過觸發清理
- 如果不在清單:
  - 比對全域 threshold (200)
  - 超過自動加入清單 + 設定 notify_threshold=50
  - 立刻執行清理

## 清理動作
- 寫入 Ignore 註冊表
  - 自動靜默模式 (auto=True)
- 清除 Enum 註冊表
- 第二次掃描補清理

## COMDB 處理
- 每日執行一次 COMDB 清理
- 鎖檔防止同日多次執行

## 記錄
- enum_guardian_log.txt
  - 詳細紀錄每次執行
- failed_cleanup.json
  - 記錄清理失敗項目

## GUI 設定工具 (config_gui_tool.py)
- 設定全域 threshold
- 設定排程時間與星期
- 管理 monitored_devices
  - vid_pid
  - notify_threshold
- 儲存 config.json

## 核心檔案
- enum_auto_run.py
  - 排程掃描/清理主程式
- cleaner.py
  - ENUM清理 / COMDB清理
- monitor.py
  - 取得 Enum 數量
- scheduler.py
  - 判斷排程執行條件
- usb_flags_manager.py
  - 寫入 Ignore 註冊表
- config_gui_tool.py
  - 圖形設定工具
- config.json
  - 系統設定檔
- failed_cleanup.json
  - 清理失敗記錄

## 功能特性
- 完全靜默執行
- 無彈窗干擾
- 執行完自動退出
- 支援自動新增監控
- 支援多次掃描清理
- 支援排程管理