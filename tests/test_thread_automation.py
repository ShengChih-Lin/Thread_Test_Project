import os
import time
import re
import logging
from datetime import datetime
import serial

# ==========================================
# 📊 1. 工業級日誌基礎建設 (Logging Setup)
# ==========================================
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 用時間戳記命名 Log 檔案
current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = os.path.join(log_dir, f"test_run_{current_time}.log")

# 設定日誌層級與格式
logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

# 建立檔案處理器 (寫入 logs 資料夾)
file_handler = logging.FileHandler(log_filename, encoding="utf-8")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# 建立控制台處理器 (噴到終端機螢幕)
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


# ==========================================
# 🔧 2. 測試環境配置
# ==========================================
LEADER_PORT = '/dev/cu.usbmodemCE9F54F0B3521'  # 第一支 Dongle
CHILD_PORT  = '/dev/cu.usbmodemE64B926176AD1'  # 第二支 Dongle
BAUDRATE    = 115200

# ==========================================
# 🛠️ 3. 輔助控制函式 (Helper Function)
# ==========================================
def send_command(ser, cmd, delay=0.5):
    """封裝發送指令與讀取回傳值的輔助函式"""
    full_cmd = cmd + "\n"
    ser.write(full_cmd.encode('utf-8'))
    time.sleep(delay)
    output = ser.read_all().decode('utf-8', errors='ignore')
    return output


# ==========================================
# 🎯 4. 自動化測試核心邏輯 (符合 pytest 規範)
# ==========================================
def test_thread_mesh_ping_validation():
    """測項：驗證 Thread 雙節點組網與跨空對 Ping 數據傳輸"""
    
    logging.info("🚀 [START] 開始執行 Thread 雙節點組網自動化測試...")

    # 先初始化為 None，避免連線失敗時 finally 區塊發生 UnboundLocalError
    leader = None
    child = None

    # 1. 初始化並建立兩個實體序列埠連線
    try:
        leader = serial.Serial(LEADER_PORT, BAUDRATE, timeout=1)
        child = serial.Serial(CHILD_PORT, BAUDRATE, timeout=1)
        logging.info("✅ 成功連線至兩台實體硬體裝置。")
    except Exception as e:
        logging.error(f"❌ 連線失敗，請檢查 Port 號是否正確。錯誤原因: {e}")
        assert False, f"Serial連線失敗: {e}"

    try:
        # 2. 初始化 Leader (第一支) 並建立網路
        logging.info("🧹 正在初始化 Leader 設備...")
        send_command(leader, "factoryreset", delay=1.0)
        send_command(leader, "dataset init new")
        send_command(leader, "dataset commit active")
        send_command(leader, "ifconfig up")
        send_command(leader, "thread start")
        send_command(leader, "leaderstart")

        logging.info("⏳ 等待 8 秒讓 Leader 成立網路 (Forming)...")
        time.sleep(8)

        # 驗證 Leader 狀態
        leader_state = send_command(leader, "state").strip()
        if "leader" in leader_state:
            logging.info("👑 Leader 當前狀態: leader")
        else:
            logging.error(f"❌ [FAIL] 第一支設備未能成功變成 Leader！當前狀態為: {leader_state}")
            assert False, "Leader 建立網路失敗"

        # 3. 獲取 Leader 的 Hex TLV 憑證
        logging.info("🔑 正在從 Leader 擷取 Hex TLV 網路憑證...")
        dataset_hex_output = send_command(leader, "dataset active -x")
        
        hex_match = re.search(r'([0-9a-fA-F]{50,})', dataset_hex_output)
        if not hex_match:
            logging.error("❌ [FAIL] 無法解析出有效的 Hex Dataset！")
            assert False, "無法獲取網路憑證"
        
        tlv_credentials = hex_match.group(1)
        logging.info(f"📦 成功自動捕獲憑證: {tlv_credentials[:20]}...{tlv_credentials[-20:]}")

        # 4. 初始化 Child (第二支) 並一鍵注入憑證
        logging.info("🧹 正在初始化 Child 設備並注入憑證...")
        send_command(child, "factoryreset", delay=1.0)
        send_command(child, f"dataset set active {tlv_credentials}")
        send_command(child, "ifconfig up")
        send_command(child, "thread start")
        
        logging.info("⏳ 等待 5 秒讓 Child 尋找並加入網路 (Joining)...")
        time.sleep(5)

        # 驗證 Child 狀態
        child_state = send_command(child, "state").strip()
        if "child" in child_state or "router" in child_state:
            logging.info(f"👶 Child 當前狀態: {child_state}")
            logging.info("🎉 [PASS] 實體雙節點 Mesh 網路成功建立！")
        else:
            logging.error(f"❌ [FAIL] 第二支設備未能成功加入網路！當前狀態為: {child_state}")
            assert False, "Child 加入網路失敗"

        # 5. 抓取 Child 的 ML-EID IPv6 位址
        logging.info("🔍 正在讀取 Child 的 ML-EID 地址...")
        ip_output = send_command(child, "ipaddr mleid")
        ip_match = re.search(r'(fd[0-9a-fA-F:]+)', ip_output)
        if not ip_match:
            logging.error("❌ [FAIL] 無法成功獲取 Child 的 IPv6 地址！")
            assert False, "無法獲取 Child IPv6 地址"
        
        child_ipv6 = ip_match.group(1)
        logging.info(f"🎯 目標 Child IP 地址: {child_ipv6}")

        # 6. 核心測試：從 Leader 發起跨空對 Ping 數據流量驗證
        logging.info(f"🔥 測試核心啟動：從 Leader 發射訊號 Ping 目的地 {child_ipv6}...")
        ping_output = send_command(leader, f"ping {child_ipv6}", delay=2.0)
        
        logging.info("--- 實體設備傳輸 Log ---")
        for line in ping_output.strip().split('\n'):
            logging.info(f"| {line}")
        logging.info("-----------------------")

        # 7. 專業 QA 斷言 (Assert) 結果
        logging.info("📊 自動化分析測試結果 (Assertion)...")
        
        # 這是 pytest 的靈魂：如果條件不成立，pytest 會自動判定這條測試為 FAIL
        assert "Packet loss = 0.0%" in ping_output, "測試失敗：通訊存在丟包，未達 0% 丟包標準！"
        
        logging.info("🏆🏆🏆 [FINAL RESULT: PASS] 🏆🏆🏆")

    except Exception as e:
        logging.critical(f"💥 腳本執行期間發生未預期崩潰: {e}", exc_info=True)
        raise e
    finally:
        # 8. 測試完畢後安全關閉資源
        if leader is not None:
            leader.close()
        if child is not None:
            child.close()
        logging.info("🔌 序列埠資源已安全釋放，測試結束。")