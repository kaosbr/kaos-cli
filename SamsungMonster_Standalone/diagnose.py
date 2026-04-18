import usb.core
import usb.util

def diagnose():
    print("Checking USB devices with PyUSB...")
    devices = usb.core.find(find_all=True)
    if not devices:
        print("No USB devices found by PyUSB.")
        return
    
    for dev in devices:
        try:
            mfg = usb.util.get_string(dev, dev.iManufacturer) if dev.iManufacturer else "Unknown"
            prod = usb.util.get_string(dev, dev.iProduct) if dev.iProduct else "Unknown"
            print(f"Device: {dev.idVendor:04x}:{dev.idProduct:04x} | Mfg: {mfg} | Prod: {prod}")
        except Exception as e:
            print(f"Device: {dev.idVendor:04x}:{dev.idProduct:04x} | Error: {e}")

if __name__ == "__main__":
    diagnose()
