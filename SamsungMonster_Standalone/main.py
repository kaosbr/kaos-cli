"""Samsung Monster Standalone - Entry Point (Final Stability)"""
import sys
import logging
import signal
import threading
from PyQt6.QtWidgets import QApplication
from core.device_manager import DeviceManager
from core.orchestrator import TaskOrchestrator
from ui.gui import SamsungMonsterGUI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("samsung_monster.log")
    ]
)

if __name__ == "__main__":
    # Prevent GUI crash on Linux Ctrl+C
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    app = QApplication(sys.argv)
    
    device_manager = DeviceManager()
    orchestrator = TaskOrchestrator(device_manager)
    
    print("🚀 Initializing Samsung Monster Elite Engine...")
    gui = SamsungMonsterGUI(orchestrator)
    gui.show()

    # Start USB monitoring after GUI binds callbacks to avoid missing initial events.
    monitor_thread = threading.Thread(target=device_manager.start_monitoring_sync, daemon=True)
    monitor_thread.start()
    
    sys.exit(app.exec())
