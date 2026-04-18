import usb.core
import usb.util

def deep_diagnose():
    dev = usb.core.find(idVendor=0x04e8, idProduct=0x685d)
    if not dev:
        print("Device not found.")
        return

    print(f"Device found: {dev.idVendor:04x}:{dev.idProduct:04x}")
    try:
        if dev.is_kernel_driver_active(0):
            dev.detach_kernel_driver(0)
        
        # Try to read product string which sometimes contains model/bit info
        print(f"Manufacturer: {usb.util.get_string(dev, dev.iManufacturer)}")
        print(f"Product: {usb.util.get_string(dev, dev.iProduct)}")
        print(f"Serial: {dev.serial_number}")
        
    except Exception as e:
        print(f"Error reading strings: {e}")

if __name__ == "__main__":
    deep_diagnose()
