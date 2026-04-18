"""Optional PyUSB loader with safe stubs for non-hardware environments."""
import sys
from types import ModuleType
from typing import Any

def _build_stub_modules():
    core = ModuleType("usb.core")
    util = ModuleType("usb.util")

    class Device: pass
    class Endpoint: pass
    class USBError(Exception): pass

    def find(*args, **kwargs):
        return [] if kwargs.get("find_all") else None

    core.Device = Device
    core.USBError = USBError
    core.find = find

    util.Endpoint = Endpoint
    util.ENDPOINT_OUT = 0x00
    util.ENDPOINT_IN = 0x80
    util.get_string = lambda *args, **kwargs: ""
    util.find_descriptor = lambda *args, **kwargs: None
    util.endpoint_direction = lambda endpoint: endpoint
    util.claim_interface = lambda *args, **kwargs: None
    util.release_interface = lambda *args, **kwargs: None
    util.dispose_resources = lambda *args, **kwargs: None

    return core, util

try:
    import usb.core as usb_core
    import usb.util as usb_util
    PYUSB_AVAILABLE = True
except ModuleNotFoundError:
    usb_core, usb_util = _build_stub_modules()
    PYUSB_AVAILABLE = False
