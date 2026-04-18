"""Device Manager - Samsung Monster Standalone"""
import logging
import asyncio
import time
from typing import Optional, Dict, List, Callable
from drivers.usb_handler import USBHandler, USBDevice
from core.enums import ConnectionMode

logger = logging.getLogger(__name__)

class DeviceManager:
    """Detect and manage Samsung devices"""

    def __init__(self, event_callback: Optional[Callable] = None):
        self.devices: Dict[str, USBDevice] = {}
        self.event_callback = event_callback
        self._is_running = False

    def start_monitoring(self):
        """Starts the async monitoring loop"""
        self._is_running = True
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._monitor_loop())
        except RuntimeError:
            # Fallback if no loop is running (will be handled by caller)
            pass

    def start_monitoring_sync(self):
        """Blocking monitoring loop for dedicated threads"""
        self._is_running = True
        while self._is_running:
            try:
                current_devices = USBHandler.list_devices()
                self._reconcile_devices(current_devices)
            except Exception as e:
                logger.debug(f"Monitor loop error: {e}")
            time.sleep(4)

    def stop_monitoring(self):
        self._is_running = False

    def scan_now(self):
        """Single synchronous USB scan to trigger immediate UI state update."""
        try:
            current_devices = USBHandler.list_devices()
            self._reconcile_devices(current_devices)
        except Exception as e:
            logger.debug(f"Scan now error: {e}")

    async def _monitor_loop(self):
        while self._is_running:
            try:
                current_devices = USBHandler.list_devices()
                self._reconcile_devices(current_devices)
            except Exception as e:
                logger.debug(f"Monitor loop error: {e}")
            await asyncio.sleep(2)

    def _reconcile_devices(self, current: List[USBDevice]):
        current_ids = {d.serial: d for d in current}
        
        # New devices
        for sid, dev in current_ids.items():
            if sid not in self.devices:
                logger.info(f"🟢 Device Connected: {sid} ({dev.mode.value})")
                self.devices[sid] = dev
                if self.event_callback: self.event_callback("CONNECTED", dev)
            elif self.devices[sid].mode != dev.mode:
                logger.info(f"🔄 Mode Changed: {sid} -> {dev.mode.value}")
                self.devices[sid] = dev
                if self.event_callback: self.event_callback("MODE_CHANGED", dev)

        # Removed devices
        removed = [sid for sid in self.devices if sid not in current_ids]
        for sid in removed:
            lost_dev = self.devices.pop(sid)
            logger.info(f"🔴 Device Disconnected: {sid}")
            if self.event_callback: self.event_callback("DISCONNECTED", lost_dev)

    def get_device(self, device_id: str) -> Optional[USBDevice]:
        return self.devices.get(device_id)
