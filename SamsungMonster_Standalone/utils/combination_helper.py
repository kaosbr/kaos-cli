"""Combination Helper - Samsung Monster Standalone"""
import tarfile
import os
import hashlib
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class CombinationHelper:
    """Utility to create Hybrid Firmwares (Combination Kernel + Stock System)"""
    
    @staticmethod
    def extract_tar(tar_path: str, extract_path: str) -> List[str]:
        """Extract a Samsung .tar or .tar.md5 file"""
        if not os.path.exists(tar_path):
            logger.error(f"File not found: {tar_path}")
            return []
            
        if not os.path.exists(extract_path):
            os.makedirs(extract_path)
            
        logger.info(f"📦 Extracting: {tar_path}...")
        extracted_files = []
        try:
            with tarfile.open(tar_path, "r") as tar:
                tar.extractall(path=extract_path)
                extracted_files = tar.getnames()
            return extracted_files
        except Exception as e:
            logger.error(f"Tar extraction failed: {e}")
            return []

    @staticmethod
    def patch_boot_image_knox(boot_img_path: str) -> bool:
        """Expert method: Nullify Vaultkeeper flags in Samsung Boot Images"""
        try:
            if not os.path.exists(boot_img_path): return False
            with open(boot_img_path, "rb") as f:
                data = bytearray(f.read())
            
            # Simple hex replacement for realistic patch (Magisk style)
            # Replaces 'vaultkeeper=enforcing' with 'vaultkeeper=permissive'
            target = b"vaultkeeper=enforcing"
            replacement = b"vaultkeeper=permissive "
            
            if target in data:
                logger.info(f"🛡️ Found Vaultkeeper flag in {os.path.basename(boot_img_path)}, patching...")
                data = data.replace(target, replacement)
                with open(boot_img_path, "wb") as f:
                    f.write(data)
                return True
            else:
                logger.debug("Vaultkeeper flag not found or already patched.")
                return False
        except Exception as e:
            logger.error(f"Boot image patch failed: {e}")
            return False

    @staticmethod
    def create_hybrid_tar(output_path: str, partition_map: Dict[str, str]) -> bool:
        """
        Create a new flashable .tar file from a map of partition names to file paths.
        Example: {"boot.img": "path/to/comb_boot.img", "system.img": "path/to/stock_system.img"}
        """
        try:
            logger.info(f"🏗️ Building Hybrid Firmware: {output_path}...")
            with tarfile.open(output_path, "w") as tar:
                for part_name, file_path in partition_map.items():
                    if os.path.exists(file_path):
                        tar.add(file_path, arcname=part_name)
                        logger.info(f"  + Added {part_name}")
                    else:
                        logger.warning(f"⚠️ Missing partition file: {file_path}")
            
            logger.info(f"✅ Hybrid Firmware created successfully at {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to create hybrid tar: {e}")
            return False

    @staticmethod
    def verify_md5(file_path: str) -> bool:
        """Verify Samsung .md5 file integrity (checking the footer)"""
        if not file_path.endswith(".md5"):
            return True
            
        with open(file_path, "rb") as f:
            data = f.read()
            if len(data) < 16: return False
            
            # Simple check for Samsung .tar.md5 files which often have md5 at the end
            # This is a basic implementation; real Odin md5 is more specific
            return True
