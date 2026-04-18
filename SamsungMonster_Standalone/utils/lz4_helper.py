"""LZ4 Decompression Engine for Samsung Firmwares"""
import os
import logging

logger = logging.getLogger(__name__)

try:
    import lz4.frame
    LZ4_AVAILABLE = True
except ImportError:
    LZ4_AVAILABLE = False

class LZ4Helper:
    """Expert utility to decompress Samsung .img.lz4 files on the fly"""
    
    @staticmethod
    def decompress_file(lz4_path: str, output_path: str = None) -> str:
        if not LZ4_AVAILABLE:
            logger.error("❌ LZ4 library not installed. Cannot decompress Samsung firmware.")
            return lz4_path
            
        if not lz4_path.endswith(".lz4"):
            return lz4_path
            
        if not output_path:
            output_path = lz4_path[:-4] # Remove .lz4 extension
            
        try:
            logger.info(f"🗜️ Decompressing LZ4: {os.path.basename(lz4_path)} -> {os.path.basename(output_path)}...")
            with open(lz4_path, "rb") as f_in:
                # Read the whole file and decompress
                # Note: For huge files (system.img.lz4), a chunked approach is better,
                # but standard Samsung LZ4 is framed and often decompressed wholly in memory
                # or by chunking.
                decompressed = lz4.frame.decompress(f_in.read())
                
            with open(output_path, "wb") as f_out:
                f_out.write(decompressed)
                
            logger.info("✅ LZ4 Decompression successful.")
            return output_path
        except Exception as e:
            logger.error(f"❌ LZ4 Decompression failed: {e}")
            return lz4_path
