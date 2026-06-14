🟢 1. logging.info() —「綠色燈號：狀況回報」
含意： 單純記錄程式目前正常、預期中的執行進度。

QA 使用場景： 只要測試在順利進行，按部就班發生的事，通通都用 info。

logging.info("🚀 測試開始...")

logging.info("✅ 序列埠連線成功。")

logging.info("⏳ 等待 8 秒中...")

白話比喻： 飛機儀表板顯示：「目前高度 3,000 英呎，一切正常。」

🟡 2. logging.warning() —「黃色燈號：不妙，但不影響執行」
含意： 發生了不尋常的狀況，但目前還沒導致測試崩潰。它是一個預警，提醒你之後可能會有潛在的風險。

QA 使用場景： 硬體測試中很常用來記錄「重試（Retry）」或「邊緣訊號」的狀況。

例子： 你的 Child 連線第一次失敗，但腳本寫了自動重試，第二次成功了。這時你不需要判定 FAIL，但應該下一個 Warning 警告。

logging.warning("⚠️ 第一次 Ping 失敗，正在進行第二次自動重試...")

logging.warning("⚠️ 偵測到周遭 Wi-Fi 干擾過高，訊號雜訊比 (RSSI) 偏低。")

白話比喻： 飛機儀表板亮黃燈：「機油有點低喔，但還可以繼續飛，待會落地記得檢查。」

🔴 3. logging.error() —「紅色燈號：災情發生、測試 FAIL」
含意： 發生了嚴重的錯誤，已經導致當前的測試案例無法繼續往下跑，必須直接判定 FAIL。

QA 使用場景： 斷言（Assertion）失敗，或是硬體完全沒有給出預期回應的時候。

logging.error("❌ [FAIL] 第一支設備未能成功變成 Leader！")

logging.error("❌ 無法解析出有效的 Hex Dataset，測試中斷。")

logging.error("❌ 連線失敗，請檢查 Port 號是否正確。")

# 🚀 Thread 雙節點組網自動化測試專案

本專案用於自動化建置與驗證 Thread Mesh 網路（基於 OpenThread CLI），並透過實體 Sniffer 與 OTBR 進行封包擷取與測試分析。

---

## 🛠️ 環境硬體配置 (Hardware Setup)
* **Master Controller**: Raspberry Pi 4 / 5 (使用 Thread Harness 1.3/1.4 Pre-cert Image)
* **DUT 1 (Leader)**: nRF52840 Dongle (Port: `/dev/cu.usbmodemCE9F54F0B3521`)
* **DUT 2 (Child)**: nRF52840 Dongle (Port: `/dev/cu.usbmodemE64B926176AD1`)
* **Sniffer**: 官方 802.15.4 USB Sniffer (固定頻道：Channel 11)

---

## 🔑 黃金測試憑證 (Golden Credentials)
為確保 Wi-Fi 與空中無線電能被 Wireshark 自動解密，測試一律使用以下固定憑證：
* **Network Name**: `Thread-Cert`
* **Master Key**: `00112233445566778899aabbccddeeff`
* **PAN ID**: `0xface`
* **Channel**: `11`

---

## 📂 專案架構說明 (Architecture)
* `/testcases`: 存放自動化測試邏輯案例。
* `/logs`: 存放每次測試執行的時間戳記日誌（包含 `INFO`、`WARNING`、`ERROR`）。
* `/pcaps`: 存放 Wireshark/tcpdump 錄製的空中 802.15.4 封包。
* `/reports`: 自動生成的測試結果視覺化報告。

---

## 🏃‍♂️ 如何執行測試 (Quick Start)
1. 確保兩支 Dongle 已插上 Mac，並確認 Port 號與腳本配置一致。
2. 開啟 Wireshark 並啟動 nRF Sniffer (選定 Channel 11)。
3. 執行自動化腳本：
   ```bash
   python3 test_thread_automation.py

   ## ❌ 障礙排除：Pytest HTML 報告生成失敗 (Troubleshooting)

### 問題現象 (Issue)
在 `qa_env` 虛擬環境中執行以下標準 pytest 指令時：
```bash
pytest test_thread_automation.py --html=reports/report.html --self-contained-html

# OTBR Headless (無螢幕) 盲接復活戰實戰筆記

這是一份專為 **Minimal Pre-cert Image**（實驗室極簡認證映像檔）打造的無螢幕排版筆記。當系統被高度閹割，連 `raspi-config`、`ifup/ifdown` 工具都被拔除時，此流程能強迫樹莓派從底層核心連上 Wi-Fi。

---

## 🎯 終極目標
在**沒有螢幕、沒有鍵盤、不知道設備 IP** 的極端狀況下，強迫全新燒錄的樹莓派（OTBR）連上家中的 Wi-Fi（`liru_5G`），並開啟 SSH 遠端控制權限。

---

## 🗺️ 全案排查心智圖與流程

當傳統的「SD 卡開機自動讀小抄」失效時，標準的 QA 除錯路徑如下：
[全新 Flash 樹莓派]
│
├──> (嘗試) SD 卡根目錄塞入 ssh / preconf-wlan0 / wpa_supplicant.conf
│
├──> [失敗] 找不到預設名稱 (open-thread.local / raspberrypi.local)
│           ⚠️ 原因：Image 太純淨，拔除了自動聯網管理工具
│
└──> [物理盲接法] 用實體網路線直接對接 Mac 與 樹莓派
│
├──> Mac 獲得 Self-assigned IP (169.254.X.X)
├──> 成功透過網路線 SSH 破門：ssh pi@raspberrypi.local
│
└──> [底層硬解] 直接呼叫 Linux 核心工具強行開通 Wi-Fi 成功！

## 📝 實戰四大關鍵步驟

### 📌 階段一：建立物理除錯通道（對接盲登）
當無線網路和小抄完全失效，且進不去分享器後台時，**實體網路線對接**是最穩固的實驗室除錯環境。

1. 用實體網路線直接連線 Mac 與樹莓派網路孔。
2. 樹莓派送電，Mac 的乙太網路會顯示黃燈的 **`Self-assigned IP`（`169.254.X.X`）**。
3. 利用預設主機名稱，成功透過實體線通道破門登入：

###📌 階段二：環境現況 QA 盤點（洞察問題）
登入系統後，發現 sudo raspi-config 設定 Wi-Fi 時噴出錯誤：

❌ No supported network connection manager found

下達 ifconfig -a 檢查硬體現況：

eth0（實體網卡）：順利運作中。

wlan0（無線網卡）：硬體存在，但處於沉睡狀態（缺少 <UP, RUNNING> 標籤）。

wpan0（Thread 網卡）：已預先啟動。

試圖執行 ifup/ifdown 卻噴出 command not found。

結論：系統被高度精簡，拔除了所有上層網路管理軟體，必須改由核心指令直接對晶片下令。

###📌 階段三：核心工具暴力破解（關鍵勝率）
既然沒有管理軟體幫忙，我們就直接繞過它們，呼叫 Linux 網路最底層的「核心三劍客」強行聯網。

1. 第一劍：無中生有設定檔
利用 wpa_passphrase 直接生成帶有加密密碼的標準 Wi-Fi 連線設定檔，強行塞給核心：

Bash
`sudo wpa_passphrase "liru_5G" "0922760028" | sudo tee /etc/wpa_supplicant/wpa_supplicant.conf`
2. 第二劍：逼無線網卡起床連線
直接呼叫 wpa_supplicant 核心主程式在背景開跑，強迫網卡晶片（wlan0）去跟客廳的 TP-Link 分享器（liru_5G）進行無線電對接（握手）：

Bash
`sudo wpa_supplicant -B -i wlan0 -c /etc/wpa_supplicant/wpa_supplicant.conf`
(出現 Successfully initialized wpa_supplicant 即代表晶片成功對接！)

3. 第三劍：強行索取實體 IP
呼叫最核心的 DHCP 分配工具，跟分享器討要家裡的區域網路 IP：
Bash
`sudo dhclient wlan0`

##📌 階段四：黃金驗收與解鎖無限自由
最後使用 `ifconfig wlan0` 進行 QA 驗收，成功看到：

Plaintext
wlan0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>
       inet 192.168.0.79  netmask 255.255.255.0

       <UP, RUNNING> 狀態全亮，並順利抱回黃金 IP 192.168.0.79！
##💡 經驗值精華（QA 筆記心得）
永遠不要信任系統的自動化工具：在認證映像檔（Pre-cert Image）的世界裡，系統越純淨，上層圖形或文字選單工具死得越快。

實體線是最好的備援方案：只要有網路線點對點（Link-Local），就算沒有分享器後台密碼，Mac 也能跟樹莓派直接建立高效通訊。

終極大絕招：只要 Linux 內建的 wpa_supplicant 和 dhclient 核心沒被拔掉，任何 Wi-Fi 都能從底層用指令硬解！

##🚀 懶人起飛：一鍵在 Mac 畫面上即時看封包（串流大法）
請先確保你 Mac 上的 Wireshark 已經照上一步填入金鑰（eca48fa195414a6d09a29d219adef7fc），並且已經在樹莓派下過 sudo ot-ctl thread start。

接著，請在你的 Mac 本機終端機（不需要 SSH 進去，開一個新的 Mac 視窗），直接複製並執行這行黃金串流指令：

`ssh pi@192.168.0.79 "sudo tcpdump -I -i wpan0 -U -w -" | /Applications/Wireshark.app/Contents/MacOS/Wireshark -k -i -`