"""USB Handler - Samsung Monster Standalone"""
import threading
import time
import asyncio
import logging
from typing import List, Optional, Callable
from dataclasses import dataclass
from utils.usb_utils import usb_core, usb_util
from core.enums import ConnectionMode

logger = logging.getLogger(__name__)

USB_GLOBAL_LOCK = threading.RLock()

@dataclass
class USBDevice:
    vendor_id: int
    product_id: int
    serial: str
    mode: ConnectionMode
    chipset: Optional[str] = None
    path: str = ""

class USBHandler:
    """USB device handler with Async support"""
    
    SAMSUNG_IDS = {
        (0x04e8, 0x685d): ConnectionMode.ODIN,
        (0x04e8, 0x6860): ConnectionMode.ADB,
        (0x04e8, 0x685e): ConnectionMode.MODEM,
        (0x04e8, 0x6601): ConnectionMode.EUB,
        (0x05c6, 0x9008): ConnectionMode.EDL, # Qualcomm HS-USB QDLoader 9008
        (0x0e8d, 0x0003): ConnectionMode.BROM, # MediaTek USB Port (BROM)
        (0x1782, 0x4d00): ConnectionMode.SPD, # Unisoc/Spreadtrum SPD
    }
    
    def __init__(self, vendor_id: int, product_id: int, timeout: int = 10000, retries: int = 5):
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.device = None
        self.ep_out = None
        self.ep_in = None
        self.timeout = timeout
        self.retries = retries
        self.lock = threading.RLock()
        self._progress_callback = None
    
    @staticmethod
    def list_devices() -> List[USBDevice]:
        """List connected Samsung devices"""
        devices = []
        with USB_GLOBAL_LOCK:
            try:
                all_devices = usb_core.find(find_all=True) or []
            except: return devices

            for dev in all_devices:
                vid = dev.idVendor
                pid = dev.idProduct
                mode = USBHandler.SAMSUNG_IDS.get((vid, pid), ConnectionMode.UNKNOWN)
                
                # Heuristic for Samsung if not in strict map
                if mode == ConnectionMode.UNKNOWN:
                    try:
                        mfg = usb_util.get_string(dev, dev.iManufacturer).lower() if dev.iManufacturer else ""
                        if "samsung" in mfg:
                            mode = ConnectionMode.NORMAL 
                    except: pass

                if mode != ConnectionMode.UNKNOWN or vid == 0x04e8:
                    try:
                        serial = dev.serial_number or f"USB_{vid:04x}_{pid:04x}"
                        devices.append(USBDevice(
                            vendor_id=vid,
                            product_id=pid,
                            serial=serial,
                            mode=mode,
                            chipset="Samsung",
                            path=f"usb://{vid:04x}:{pid:04x}"
                        ))
                    except: continue
            return devices

    def connect(self, with_reset: bool = False) -> bool:
        with USB_GLOBAL_LOCK: # Garantir que o monitor USB não interfira na conexão
            with self.lock:
                try:
                    self.device = usb_core.find(idVendor=self.vendor_id, idProduct=self.product_id)
                    if self.device is None: return False
                    
                    try:
                        if self.device.is_kernel_driver_active(0):
                            self.device.detach_kernel_driver(0)
                    except: pass
                    
                    if with_reset:
                        try:
                            self.device.reset()
                            time.sleep(1)
                            self.device = usb_core.find(idVendor=self.vendor_id, idProduct=self.product_id)
                        except: pass
                    
                    try:
                        self.device.set_configuration()
                    except: pass
                    
                    usb_util.claim_interface(self.device, 0)
                    cfg = self.device.get_active_configuration()
                    intf = cfg[(0, 0)]
                    self.ep_out = usb_util.find_descriptor(intf, custom_match=lambda e:
                        usb_util.endpoint_direction(e.bEndpointAddress) == usb_util.ENDPOINT_OUT)
                    self.ep_in = usb_util.find_descriptor(intf, custom_match=lambda e:
                        usb_util.endpoint_direction(e.bEndpointAddress) == usb_util.ENDPOINT_IN)
                    return self.ep_out is not None and self.ep_in is not None
                except Exception as e:
                    logger.error(f"Connect error: {e}")
                    return False

    async def async_connect(self, with_reset: bool = False) -> bool:
        return await asyncio.to_thread(self.connect, with_reset)

    def disconnect(self):
        with self.lock:
            if self.device:
                try:
                    usb_util.release_interface(self.device, 0)
                    usb_util.dispose_resources(self.device)
                except: pass
                self.device = None
    
    async def async_disconnect(self):
        await asyncio.to_thread(self.disconnect)

    def send(self, data: bytes, timeout: int = None) -> int:
        timeout = timeout or self.timeout
        try:
            with self.lock:
                if not self.device or not self.ep_out: return -1
                return self.ep_out.write(data, timeout=timeout)
        except: return -1
    
    async def async_send(self, data: bytes, timeout: int = None) -> int:
        return await asyncio.to_thread(self.send, data, timeout)

    def recv(self, size: int, timeout: int = None) -> bytes:
        timeout = timeout or self.timeout
        try:
            with self.lock:
                if not self.device or not self.ep_in: return b''
                return bytes(self.ep_in.read(size, timeout=timeout))
        except: return b''

    async def async_recv(self, size: int, timeout: int = None) -> bytes:
        return await asyncio.to_thread(self.recv, size, timeout)
