"""Driver Health Doctor - Samsung Monster Standalone"""
import os
import subprocess
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class DriverDoctor:
    """Expert utility to diagnose and fix USB driver issues on Linux"""

    @staticmethod
    def diagnose() -> List[Dict]:
        """Check for common driver issues"""
        results = []
        
        # 1. Check udev rules
        udev_path = "/etc/udev/rules.d/51-frp-monster.rules"
        if not os.path.exists(udev_path):
            results.append({"issue": "Missing udev rules", "fixable": True, "id": "udev"})
        
        # 2. Check group membership
        groups = subprocess.getoutput("groups")
        if "plugdev" not in groups:
            results.append({"issue": "User not in 'plugdev' group", "fixable": True, "id": "group"})
            
        # 3. Check for modem-manager conflict
        status = subprocess.getoutput("systemctl is-active ModemManager")
        if status == "active":
            results.append({"issue": "ModemManager active (may block serial ports)", "fixable": True, "id": "modemmanager"})
            
        return results

    @staticmethod
    def auto_fix(issue_id: str) -> bool:
        """Attempt to fix identified issues (requires sudo for some)"""
        try:
            if issue_id == "udev":
                udev_path = "/etc/udev/rules.d/51-frp-monster.rules"
                if os.path.exists(udev_path):
                    return True
                rule = 'SUBSYSTEM=="usb", ATTR{idVendor}=="04e8", MODE="0666", GROUP="plugdev"\\n'
                cmd = (
                    f"printf '{rule}' | sudo -n tee {udev_path} >/dev/null "
                    "&& sudo -n udevadm control --reload-rules && sudo -n udevadm trigger"
                )
                return subprocess.call(cmd, shell=True) == 0
            elif issue_id == "group":
                user = os.environ.get("USER", "")
                if not user:
                    return False
                return subprocess.call(f"sudo -n usermod -aG plugdev {user}", shell=True) == 0
            elif issue_id == "modemmanager":
                return subprocess.call("sudo -n systemctl stop ModemManager", shell=True) == 0
            return False
        except Exception as e:
            logger.error(f"Fix error: {e}")
            return False
