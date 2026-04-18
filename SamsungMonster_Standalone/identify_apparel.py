import serial
import serial.tools.list_ports
import time

def get_real_identity():
    print("🔍 Searching for Samsung Modem Port...")
    ports = list(serial.tools.list_ports.comports())
    target_port = None
    for p in ports:
        if p.vid == 0x04e8:
            target_port = p.device
            break
    
    if not target_port:
        print("❌ Samsung Modem port not found. Is it in MTP mode?")
        return

    print(f"📡 Connecting to {target_port}...")
    try:
        ser = serial.Serial(target_port, 115200, timeout=2)
        
        # Command 1: Basic Model Info
        ser.write(b"AT+DEVCONINFO\r\n")
        time.sleep(0.5)
        resp1 = ser.read_all().decode(errors="ignore")
        
        # Command 2: Version Info
        ser.write(b"AT+VERSNAME=1,2,3\r\n")
        time.sleep(0.5)
        resp2 = ser.read_all().decode(errors="ignore")
        
        print("\n--- [ APPAREL IDENTITY REPORT ] ---")
        if "MN(" in resp1:
            model = resp1.split("MN(")[1].split(")")[0]
            print(f"✅ MODELO REAL: {model}")
        
        if "SWREV:" in resp1:
            bit = resp1.split("SWREV:")[1].split(",")[0]
            print(f"✅ BIT (SW REV): {bit}")
            
        print(f"📄 RAW INFO:\n{resp1}\n{resp2}")
        print("-----------------------------------\n")
        
        ser.close()
    except Exception as e:
        print(f"❌ Error communicating with modem: {e}")

if __name__ == "__main__":
    get_real_identity()
