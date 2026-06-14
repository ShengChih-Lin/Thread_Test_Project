import serial
import sys
import time

def main():
    port = '/dev/cu.usbmodemC374B5ABC2DB2'  # 請確保這是你的 Sniffer 晶片路徑
    baudrate = 115200
    
    # Spinel 指令
    SPINEL_CMD_RESET = b'\x80\x06\x01'
    SPINEL_CMD_SET_CHANNEL_14 = b'\x80\x06\x0d\x01\x0e'
    SPINEL_CMD_SCAN_START = b'\x80\x06\x24\x01'
    
    try:
        ser = serial.Serial(port, baudrate, timeout=1)
        
        # 驅動硬體
        ser.write(SPINEL_CMD_RESET)
        time.sleep(0.1)
        ser.write(SPINEL_CMD_SET_CHANNEL_14)
        time.sleep(0.1)
        ser.write(SPINEL_CMD_SCAN_START)
        time.sleep(0.1)
        ser.reset_input_buffer()
        
        print("【系統提示】已成功對晶片下達 Channel 14 監聽指令，開始監控原始數據流...", file=sys.stderr)
        
        while True:
            if ser.in_waiting > 0:
                data = ser.read(ser.in_waiting)
                # 將原始的二進位轉成人類看得懂的 16 進位字串印出來
                hex_str = data.hex(' ').upper()
                print(hex_str, end=' ', flush=True)
            else:
                time.sleep(0.01)
                
    except KeyboardInterrupt:
        print("\n【系統提示】使用者停止監聽。", file=sys.stderr)
    except Exception as e:
        print(f"\n【錯誤】{str(e)}", file=sys.stderr)

if __name__ == '__main__':
    main()