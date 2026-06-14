import serial
import time
import re
import os
import time
import logging  # 1. 引入內建日誌模組
from datetime import datetime
import serial

# 2. 建立 log 資料夾（如果不存在的話自動建立）
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 3. 用時間戳記命名你的 Log 檔案（例如：logs/test_run_20260526_144000.log）
current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = os.path.join(log_dir, f"test_run_{current_time}.log")

# 4. 設定 logging 設定：同時輸出到「畫面」與「檔案」
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 設定 Log 的輸出格式： 時間 [層級] 訊息內容
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

# 建立檔案處理器（寫入檔案）
file_handler = logging.FileHandler(log_filename, encoding="utf-8")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# 建立控制台處理器（噴到終端機畫面上）
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# --- 這樣就設定完成了！ ---

# ==========================================
# 🔧 測試環境配置 (請根據你 Mac 的實際 Port 號修改)
# ==========================================
LEADER_PORT = '/dev/cu.usbmodemCE9F54F0B3521'  # 第一支 Dongle
CHILD_PORT  = '/dev/cu.usbmodemE64B926176AD1'  # 第二支 Dongle
BAUDRATE    = 115200

def send_command(ser, cmd, delay=0.5):
    """封裝發送指令與讀取回傳值的輔助函式"""
    full_cmd = cmd + "\n"
    ser.write(full_cmd.encode('utf-8'))
    time.sleep(delay)
    output = ser.read_all().decode('utf-8', errors='ignore')
    return output

def test_main():
    #print("🚀 [START] 開始執行 Thread 雙節點組網自動化測試...")
    logging.info("🚀 [START] 開始執行 Thread 雙節點組網自動化測試...")

    if state == "leader":
        logging.info("👑 Leader 當前狀態: leader")
    else:
        alogging.error("❌ [FAIL] 第一支設備未能成功變成 Leader！")

    # 1. 初始化並建立兩個實體序列埠連線
    try:
        leader = serial.Serial(LEADER_PORT, BAUDRATE, timeout=1)
        child = serial.Serial(CHILD_PORT, BAUDRATE, timeout=1)
        print("✅ 成功連線至兩台實體硬體裝置。")
    except Exception as e:
        print(f"❌ 連線失敗，請檢查 Port 號是否正確。錯誤原因: {e}")
        return

    try:
        # 2. 初始化 Leader (第一支) 並建立網路
        print("\n🧹 正在初始化 Leader 設備...")
        send_command(leader, "factoryreset", delay=1.0)
        send_command(leader, "dataset init new")
        send_command(leader, "dataset commit active")
        # --- 尋找這段原本的程式碼 ---
        send_command(leader, "ifconfig up")
        send_command(leader, "thread start")
        # ⬇️ 緊接著在下方補上下列這一行關鍵指令 ⬇️
        send_command(leader, "leaderstart")  # <-- 強制晶片立刻跳過搜尋，直接稱王！

        print("⏳ 等待 8 秒讓 Leader 成立網路 (Forming)...")
        time.sleep(8)

        # 驗證 Leader 狀態
        leader_state = send_command(leader, "state")
        print(f"👑 Leader 當前狀態: {leader_state.strip()}")
        if "leader" not in leader_state:
            print("❌ [FAIL] 第一支設備未能成功變成 Leader！")
            return

        # 3. 獲取 Leader 的 Hex TLV 憑證
        print("🔑 正在從 Leader 擷取 Hex TLV 網路憑證...")
        dataset_hex_output = send_command(leader, "dataset active -x")
        
        # 使用正則表達式 (Regex) 自動過濾並抓取那串長長的十六進位字串
        hex_match = re.search(r'([0-9a-fA-F]{50,})', dataset_hex_output)
        if not hex_match:
            print("❌ [FAIL] 無法解析出有效的 Hex Dataset！")
            return
        
        tlv_credentials = hex_match.group(1)
        print(f"📦 成功自動捕獲憑證: {tlv_credentials[:20]}...{tlv_credentials[-20:]}")

        # 4. 初始化 Child (第二支) 並一鍵注入憑證
        print("\n🧹 正在初始化 Child 設備並注入憑證...")
        send_command(child, "factoryreset", delay=1.0)
        send_command(child, f"dataset set active {tlv_credentials}")
        send_command(child, "ifconfig up")
        send_command(child, "thread start")
        print("⏳ 等待 5 秒讓 Child 尋找並加入網路 (Joining)...")
        time.sleep(5)

        # 驗證 Child 狀態
        child_state = send_command(child, "state")
        print(f"👶 Child 當前狀態: {child_state.strip()}")
        if "child" not in child_state and "router" not in child_state:
            print("❌ [FAIL] 第二支設備未能成功加入網路！")
            return
        print("🎉 [PASS] 實體雙節點 Mesh 網路成功建立！")

        # 5. 抓取 Child 的 ML-EID IPv6 位址
        print("\n🔍 正在讀取 Child 的 ML-EID 地址...")
        ip_output = send_command(child, "ipaddr mleid")
        ip_match = re.search(r'(fd[0-9a-fA-F:]+)', ip_output)
        if not ip_match:
            print("❌ [FAIL] 無法成功獲取 Child 的 IPv6 地址！")
            return
        
        child_ipv6 = ip_match.group(1)
        print(f"🎯 目標 Child IP 地址: {child_ipv6}")

        # 6. 核心測試：從 Leader 發起跨空對 Ping 數據流量驗證
        print(f"\n🔥 測試核心啟動：從 Leader 發射訊號 Ping 目的地 {child_ipv6}...")
        ping_output = send_command(leader, f"ping {child_ipv6}", delay=2.0)
        print("\n--- 實體設備傳輸 Log ---")
        print(ping_output.strip())
        print("-----------------------")

        # 7. 專業 QA 斷言 (Assert) 結果
        print("\n📊 自動化分析測試結果 (Assertion)...")
        if "Packet loss = 0.0%" in ping_output:
            print("\n🏆🏆🏆 [FINAL RESULT: PASS] 🏆🏆🏆")
            print("原因：雙向數據鏈路通暢，0.0% 丟包，物聯網功能完全正常！")
        else:
            print("\n❌❌❌ [FINAL RESULT: FAIL] ❌❌❌")
            print("原因：通訊可能存在干擾，或未達到 0% 丟包之 QA 出廠標準。")

    except Exception as e:
        print(f"💥 腳本執行期間發生未預期崩潰: {e}")
    finally:
        # 8. 測試完畢後關閉資源 (好習慣)
        leader.close()
        child.close()
        print("\n🔌 序列埠資源已安全釋放，測試結束。")

if __name__ == "__main__":
    test_main()