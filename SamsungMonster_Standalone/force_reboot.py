import serial
import serial.tools.list_ports
import time

def force_test_reboot():
    print("🚀 Searching for Samsung Modem Port...")
    ports = list(serial.tools.list_ports.comports())
    target_port = None
    for p in ports:
        if p.vid == 0x04e8:
            target_port = p.device
            break
    
    if not target_port:
        print("❌ Modem port not found.")
        return

    print(f"📡 Sending Force Reboot commands to {target_port}...")
    try:
        ser = serial.Serial(target_port, 115200, timeout=1)
        
        # Sequence to force test modes or download
        commands = [
            b"AT+REBOOT=factory\r\n",   # Try factory mode
            b"AT+REBOOT=download\r\n",  # Try download mode
            b"AT+FACTRESET\r\n",        # Emergency Factory Reset
            b"AT+SYSSCO=4,1\r\n"        # Force USB mode switch
        ]
        
        for cmd in commands:
            print(f"Sending: {cmd.decode().strip()}")
            ser.write(cmd)
            time.sleep(0.5)
            resp = ser.read_all()
            if resp: print(f"Response: {resp.decode(errors='ignore').strip()}")
        
        ser.close()
        print("✅ Command sequence sent.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    force_test_reboot()
