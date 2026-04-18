import asyncio
import usb.core
import usb.util
import time

def brute_handshake():
    dev = usb.core.find(idVendor=0x04e8, idProduct=0x685d)
    if not dev: return
    
    print("🔥 Starting Brute-Force Handshake loop...")
    try:
        if dev.is_kernel_driver_active(0): dev.detach_kernel_driver(0)
        dev.set_configuration()
        cfg = dev.get_active_configuration()
        intf = cfg[(0,0)]
        out_ep = usb.util.find_descriptor(intf, custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT)
        in_ep = usb.util.find_descriptor(intf, custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN)

        for i in range(100):
            try:
                out_ep.write(b'ODIN', timeout=100)
                resp = in_ep.read(4, timeout=100)
                if resp == b'LOKE':
                    print(f"✅ SUCCESS! Handshake accepted on attempt {i}")
                    return True
            except:
                continue
        print("❌ Brute-force failed. Device is locked by MDM SECURE_USB.")
        return False
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    brute_handshake()
