"""Loader Manager - Samsung Monster Standalone"""
import os
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

class LoaderManager:
    """Manages external programmers and loaders for EDL/EUB modes"""
    
    BASE_PATH = "resources/loaders"

    @staticmethod
    def list_loaders(chipset: str) -> List[str]:
        """List available loaders for a specific chipset (qualcomm/exynos)"""
        path = os.path.join(LoaderManager.BASE_PATH, chipset.lower())
        if not os.path.exists(path):
            os.makedirs(path)
            return []
        
        return [f for f in os.listdir(path) if f.endswith(('.bin', '.elf', '.mbn'))]

    @staticmethod
    def get_loader_path(chipset: str, filename: str) -> Optional[str]:
        """Get absolute path to a specific loader file"""
        path = os.path.join(LoaderManager.BASE_PATH, chipset.lower(), filename)
        return path if os.path.exists(path) else None

    @staticmethod
    def auto_detect_loader(chipset: str, hwid: str) -> Optional[str]:
        """Heuristic to find the best loader based on Hardware ID (HWID)"""
        loaders = LoaderManager.list_loaders(chipset)
        for l in loaders:
            if hwid.lower() in l.lower():
                return l
        return None
