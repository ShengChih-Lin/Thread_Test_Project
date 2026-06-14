# tests/conftest.py 範例
import pytest
import subprocess
import os
import signal

@pytest.fixture(scope="session", autouse=True)
def auto_sniffer():
    print("\n[Fixture] 🚀 測試開始，自動在背景啟動 Thread Sniffer...")
    
    # 動態取得路徑，不管你在哪跑都能精準定位到 utils/live_sniffer.py
    current_dir = os.path.dirname(__file__)
    sniffer_path = os.path.join(current_dir, "../utils/live_sniffer.py")
    
    # 在背景啟動 Sniffer 抓包，並將資料寫入 logs/capture.pcap
    pcap_file = open("logs/capture.pcap", "wb")
    process = subprocess.Popen(
        ["python", sniffer_path],
        stdout=pcap_file,
        stderr=subprocess.PIPE
    )
    
    yield process  # 這裡會切換去執行你的 test_thread_automation.py 測試案例
    
    print("\n[Fixture] 🛑 測試結束，自動關閉 Sniffer 並儲存 pcap 紀錄。")
    process.send_signal(signal.SIGINT) # 送出 Ctrl+C 訊號安全關閉
    process.wait()
    pcap_file.close()