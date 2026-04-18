"""Firmware Fetcher & Cloud Engine - Samsung Monster Standalone"""
import os
import requests
import logging
import zipfile
import shutil
import re
from datetime import datetime
from typing import Optional, Dict, List
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class FirmwareFetcher:
    """Expert tool to find and download Samsung firmwares using SamFW public base"""
    
    SAMFW_BASE = "https://samfw.com/firmware"
    TEMP_DIR = "temp_firmware"
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

    @staticmethod
    def get_samfw_firmware(model: str, region: str, target_bit: Optional[str] = None, bridge_mode: bool = False) -> Optional[Dict]:
        """Scrape SamFW to find the best firmware (Latest, Downgrade or Bridge)"""
        url = f"{FirmwareFetcher.SAMFW_BASE}/{model}/{region}"
        headers = {"User-Agent": FirmwareFetcher.USER_AGENT}
        
        try:
            logger.info(f"🔍 Scraping SamFW for {model} [{region}]...")
            resp = requests.get(url, headers=headers, timeout=15)
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.text, "html.parser")
            table = soup.find("table")
            if not table:
                logger.error("❌ Firmware table not found on SamFW.")
                return None
            
            candidates = []
            rows = table.find_all("tr")[1:] # Skip header
            
            for row in rows:
                cols = row.find_all("td")
                if len(cols) < 5: continue
                
                version = cols[0].get_text(strip=True)
                os_ver = cols[1].get_text(strip=True)
                date = cols[2].get_text(strip=True)
                
                # Extract Bit from PDA (e.g. S918BXXU3AWF7 -> Bit 3)
                # PDA is usually the first part of version, the bit is 5th char from end
                pda = version.split("/")[0] if "/" in version else version
                bit = pda[-5] if len(pda) > 5 else "0"
                
                link_tag = cols[-1].find("a")
                download_url = link_tag["href"] if link_tag else ""
                
                candidates.append({
                    "version": version,
                    "os": os_ver,
                    "date": date,
                    "bit": bit,
                    "download_url": download_url if download_url.startswith("http") else f"https://samfw.com{download_url}"
                })

            if not candidates: return None

            # Filter by Target Bit if provided (Crucial for Anti-Brick)
            if target_bit:
                filtered = [c for c in candidates if c['bit'] == str(target_bit)]
                if filtered:
                    candidates = filtered
                else:
                    logger.warning(f"⚠️ No firmware found for Bit {target_bit}; using closest available list.")

            def _date_key(raw: str):
                for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%Y"):
                    try:
                        return datetime.strptime(raw, fmt)
                    except Exception:
                        continue
                return datetime.min

            # Smart Bridge Logic: Find the oldest patch for the same Bit (to maximize exploit success)
            if bridge_mode:
                # Sort by date ascending
                candidates.sort(key=lambda x: _date_key(x.get('date', '')))
                selected = candidates[0]
                logger.info(f"🌉 Bridge Mode: Selected oldest firmware {selected['version']} (Bit {selected['bit']})")
                return selected
            
            # Latest Logic:
            candidates.sort(key=lambda x: _date_key(x.get('date', '')), reverse=True)
            return candidates[0]

        except Exception as e:
            logger.error(f"Scraping error: {e}")
            return None

    @staticmethod
    def get_latest_firmware(model: str, region: str) -> Optional[Dict]:
        """Legacy compatibility - forwards to SamFW engine"""
        return FirmwareFetcher.get_samfw_firmware(model, region)

    @staticmethod
    def download_and_extract(page_url: str, progress_cb=None) -> Optional[str]:
        """Resolve direct link, download with Speed/ETA and extract"""
        headers = {"User-Agent": FirmwareFetcher.USER_AGENT}
        
        try:
            # Step 1: Resolve Direct Link from SamFW Page
            logger.info(f"🔗 Resolving direct download link from {page_url}...")
            resp = requests.get(page_url, headers=headers, timeout=10)
            resp.raise_for_status()
            # Find the download button or script variable with the real link
            # SamFW typically uses a 'server' parameter or a direct CDN link
            match = re.search(r'https://samfw\.com/download/[^"\']+', resp.text)
            direct_url = match.group(0) if match else page_url
            if direct_url.endswith("/"):
                direct_url = direct_url[:-1]

            # Resolve one more time if still on a SamFW download page.
            if "/download/" in direct_url and not re.search(r'\.(zip|tar|md5|7z|rar)$', direct_url, re.IGNORECASE):
                dl_resp = requests.get(direct_url, headers=headers, timeout=10)
                dl_resp.raise_for_status()
                direct_candidates = re.findall(r'https?://[^"\']+\.(?:zip|tar|md5|7z|rar)', dl_resp.text, flags=re.IGNORECASE)
                if direct_candidates:
                    direct_url = direct_candidates[0]
            
            if os.path.exists(FirmwareFetcher.TEMP_DIR):
                shutil.rmtree(FirmwareFetcher.TEMP_DIR)
            os.makedirs(FirmwareFetcher.TEMP_DIR)
            
            ext = ".zip" if ".zip" in direct_url.lower() else ".bin"
            target_path = os.path.join(FirmwareFetcher.TEMP_DIR, f"fw{ext}")
            
            # Step 2: Download with High-Precision Monitor
            import time
            start_time = time.time()
            with requests.get(direct_url, stream=True, headers=headers) as r:
                r.raise_for_status()
                total = int(r.headers.get('content-length', 0))
                done = 0
                
                with open(target_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024*1024): # 1MB chunks
                        if chunk:
                            f.write(chunk)
                            done += len(chunk)
                            
                            # Calculate Speed and ETA
                            elapsed = time.time() - start_time
                            speed = done / elapsed if elapsed > 0 else 0 # bytes/s
                            eta = (total - done) / speed if speed > 0 else 0
                            
                            if progress_cb:
                                progress_info = {
                                    "percent": int((done/total)*100) if total > 0 else 0,
                                    "speed": f"{speed/1024/1024:.2f} MB/s",
                                    "eta": f"{int(eta)}s",
                                    "stage": f"Downloading: {done/1024/1024:.1f}MB / {total/1024/1024:.1f}MB"
                                }
                                progress_cb(progress_info)
            
            logger.info("📦 Download complete. Extracting package...")
            if zipfile.is_zipfile(target_path):
                with zipfile.ZipFile(target_path, 'r') as z:
                    z.extractall(FirmwareFetcher.TEMP_DIR)
            
            return FirmwareFetcher.TEMP_DIR
        except Exception as e:
            logger.error(f"❌ Download/Extract error: {e}")
            return None

    @staticmethod
    def map_extracted_files(path: str) -> Dict[str, str]:
        """Map files (BL, AP, CP, CSC) based on Samsung naming convention"""
        mapping = {}
        for root, _, files in os.walk(path):
            for f in files:
                name = f.upper()
                full = os.path.join(root, f)
                if "BL_" in name and "BL" not in mapping:
                    mapping["BL"] = full
                elif "AP_" in name and "AP" not in mapping:
                    mapping["AP"] = full
                elif "CP_" in name and "CP" not in mapping:
                    mapping["CP"] = full
                elif "HOME_CSC_" in name and "CSC" not in mapping:
                    mapping["CSC"] = full
                elif "CSC_" in name and "CSC" not in mapping:
                    mapping["CSC"] = full
                elif "USERDATA_" in name and "USERDATA" not in mapping:
                    mapping["USERDATA"] = full
        return mapping
