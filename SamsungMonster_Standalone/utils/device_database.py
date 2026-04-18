"""Simplified Device Database for Samsung Monster"""
import logging

logger = logging.getLogger(__name__)

class DeviceDatabase:
    """Minimal database for Samsung chipsets"""
    
    CHIPSETS = {
        # Exynos
        0x3830: {"chipset": "Exynos 850 (S5E3830)", "type": "Exynos"},
        0x7870: {"chipset": "Exynos 7870", "type": "Exynos"},
        0x7884: {"chipset": "Exynos 7884", "type": "Exynos"},
        0x7885: {"chipset": "Exynos 7885", "type": "Exynos"},
        0x7904: {"chipset": "Exynos 7904", "type": "Exynos"},
        0x8895: {"chipset": "Exynos 8895", "type": "Exynos"},
        0x9110: {"chipset": "Exynos 9110", "type": "Exynos"},
        0x9610: {"chipset": "Exynos 9610", "type": "Exynos"},
        0x9611: {"chipset": "Exynos 9611", "type": "Exynos"},
        0x9810: {"chipset": "Exynos 9810", "type": "Exynos"},
        0x9820: {"chipset": "Exynos 9820", "type": "Exynos"},
        0x9825: {"chipset": "Exynos 9825", "type": "Exynos"},
        0x990:  {"chipset": "Exynos 990", "type": "Exynos"},
        0x2100: {"chipset": "Exynos 2100", "type": "Exynos"},
        0x2200: {"chipset": "Exynos 2200", "type": "Exynos"},
        0x2400: {"chipset": "Exynos 2400 (S5E9945)", "type": "Exynos"},
        0x2500: {"chipset": "Exynos 2500 (S5E9955)", "type": "Exynos"},
        0x2600: {"chipset": "Exynos 2600 (S5E9965) - MONSTER ELITE", "type": "Exynos"},
        
        # Qualcomm (MSM/SDM/SM)
        0x001BD0E1: {"chipset": "Snapdragon 8 Gen 2", "type": "Qualcomm"},
        0x001E30E1: {"chipset": "Snapdragon 8 Gen 3", "type": "Qualcomm"},
        0x0021A0E1: {"chipset": "Snapdragon 8 Gen 4", "type": "Qualcomm"},
        0x002450E1: {"chipset": "Snapdragon 8 Gen 5 - MONSTER ELITE", "type": "Qualcomm"},
        0x000700E1: {"chipset": "Snapdragon 855", "type": "Qualcomm"},
        
        # MediaTek (MT)
        0x0767: {"chipset": "Dimensity 9000", "type": "MediaTek"},
        0x0817: {"chipset": "Dimensity 1200", "type": "MediaTek"},
        0x0927: {"chipset": "Dimensity 9200", "type": "MediaTek"},
        0x0930: {"chipset": "Dimensity 9300+", "type": "MediaTek"},
        0x0940: {"chipset": "Dimensity 9400 - MONSTER ELITE", "type": "MediaTek"},
        0x6765: {"chipset": "Helio G35", "type": "MediaTek"},
        0x6768: {"chipset": "Helio G80/G85", "type": "MediaTek"},
    }

    def identify_by_hwid(self, hwid: int) -> dict:
        """Lookup chipset info by HWID"""
        return self.CHIPSETS.get(hwid, {"chipset": f"Unknown SoC (0x{hwid:08X})", "type": "Unknown"})
