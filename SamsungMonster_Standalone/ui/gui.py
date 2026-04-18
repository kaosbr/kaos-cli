import sys
import asyncio
import time
import os
import threading
from typing import Optional, Callable
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QTextEdit, QFrame, 
                             QProgressBar, QTabWidget, QGridLayout, QScrollArea, 
                             QComboBox, QStackedWidget, QFileDialog, QTableWidget, 
                             QHeaderView, QTableWidgetItem, QCheckBox)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QPixmap
from core.orchestrator import TaskOrchestrator
from core.enums import ConnectionMode
from .widgets import ModernButton, StatusCard, SidebarMenu

class UIEventEmitter(QObject):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    device_event = pyqtSignal(str, object)

class SamsungMonsterGUI(QMainWindow):
    def __init__(self, orchestrator: TaskOrchestrator):
        super().__init__()
        self.orchestrator = orchestrator
        self.emitter = UIEventEmitter()
        self.current_device_id: Optional[str] = None
        
        # Start background event loop for async operations
        self.loop = asyncio.new_event_loop()
        self.loop_thread = threading.Thread(target=self.loop.run_forever, daemon=True)
        self.loop_thread.start()
        
        self.setWindowTitle("SAMSUNG MONSTER v10.1 - ELITE SUITE")
        self.setMinimumSize(1200, 850)
        self.setStyleSheet("background-color: #121212; color: #FFFFFF; font-family: 'Segoe UI', sans-serif;")
        
        self._setup_ui()
        self._connect_signals()
        self._update_ui_state(ConnectionMode.UNKNOWN)
        self._add_log("🚀 Samsung Monster v10.1 Elite Engine Started.")

    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar Navigation
        sidebar_items = [
            ("🏠", "DASHBOARD"),
            ("💾", "FIRMWARE"),
            ("🛡️", "SECURITY"),
            ("🔧", "SERVICE"),
            ("📚", "RESOURCES")
        ]
        self.sidebar = SidebarMenu(sidebar_items)
        main_layout.addWidget(self.sidebar)

        # Main Content Area
        content_wrapper = QVBoxLayout()
        content_wrapper.setContentsMargins(20, 20, 20, 20)
        content_wrapper.setSpacing(15)
        
        # Header: Status Card
        self.status_card = StatusCard()
        content_wrapper.addWidget(self.status_card)

        # Content Stack
        self.main_stack = QStackedWidget()
        self.main_stack.addWidget(self._init_view_dashboard())
        self.main_stack.addWidget(self._init_view_firmware())
        self.main_stack.addWidget(self._init_view_security())
        self.main_stack.addWidget(self._init_view_service())
        self.main_stack.addWidget(self._init_view_resources())
        content_wrapper.addWidget(self.main_stack)

        # Global Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar { background-color: #2A2A2A; border: 1px solid #333; border-radius: 5px; text-align: center; height: 18px; font-size: 10px; }
            QProgressBar::chunk { background-color: #0078D4; border-radius: 4px; }
        """)
        content_wrapper.addWidget(self.progress_bar)

        main_layout.addLayout(content_wrapper)
        self.sidebar.item_clicked.connect(self.main_stack.setCurrentIndex)

    # --- VIEW CONSTRUCTORS ---

    def _init_view_dashboard(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        info_group = QFrame()
        info_group.setStyleSheet("background: #1E1E1E; border: 1px solid #333; border-radius: 8px; padding: 15px;")
        info_layout = QGridLayout(info_group)
        self.lbl_det_model = QLabel("Model: ---"); info_layout.addWidget(self.lbl_det_model, 0, 0)
        self.lbl_det_bit = QLabel("Bit: ---"); info_layout.addWidget(self.lbl_det_bit, 0, 1)
        self.lbl_det_region = QLabel("Region: ---"); info_layout.addWidget(self.lbl_det_region, 1, 0)
        self.lbl_det_version = QLabel("Version: ---"); info_layout.addWidget(self.lbl_det_version, 1, 1)
        self.lbl_det_variant = QLabel("Variant: ---"); info_layout.addWidget(self.lbl_det_variant, 2, 0, 1, 2)
        layout.addWidget(info_group)
        
        btn_layout = QHBoxLayout()
        self.btn_read_info = ModernButton("🔍 READ DEVICE INFO", primary=True)
        self.btn_read_info.clicked.connect(lambda: self._execute_async(self._run_read_info()))
        btn_layout.addWidget(self.btn_read_info)
        
        self.btn_reboot_sys = ModernButton("🔄 REBOOT SYSTEM")
        self.btn_reboot_sys.clicked.connect(lambda: self._execute_async(self.orchestrator.run_reboot(self.current_device_id, "system")))
        btn_layout.addWidget(self.btn_reboot_sys)
        
        self.btn_reboot_dw = ModernButton("📥 REBOOT DOWNLOAD")
        self.btn_reboot_dw.clicked.connect(lambda: self._execute_async(self.orchestrator.run_reboot(self.current_device_id, "download")))
        btn_layout.addWidget(self.btn_reboot_dw)
        
        self.btn_force_reboot = ModernButton("🔥 FORCE REBOOT", dangerous=True)
        self.btn_force_reboot.clicked.connect(lambda: self._execute_async(self.orchestrator.run_force_reboot(self.current_device_id, self._add_log_prog)))
        btn_layout.addWidget(self.btn_force_reboot)
        
        self.btn_deep_diag = ModernButton("🩺 DEEP DIAGNOSE", primary=True)
        self.btn_deep_diag.clicked.connect(lambda: self._execute_async(self._run_deep_diagnose()))
        btn_layout.addWidget(self.btn_deep_diag)
        
        layout.addLayout(btn_layout)

        layout.addWidget(QLabel("RECENT ACTIVITY"))
        self.mini_log = QTextEdit(); self.mini_log.setReadOnly(True)
        self.mini_log.setStyleSheet("background: #000; color: #00FF41; font-family: 'Consolas', monospace; font-size: 11px;")
        layout.addWidget(self.mini_log)
        return widget

    def _init_view_firmware(self) -> QWidget:
        tabs = QTabWidget()
        tabs.addTab(self._init_tab_flash(), "💾 ODIN FLASH")
        tabs.addTab(self._init_tab_cloud(), "☁️ SMART REPAIR")
        tabs.addTab(self._init_tab_hybrid(), "🏗️ HYBRID ENGINE")
        return tabs

    def _init_view_security(self) -> QWidget:
        tabs = QTabWidget()
        tabs.addTab(self._init_tab_home(), "🔓 QUICK BYPASS")
        tabs.addTab(self._init_tab_unlock(), "🔓 FRP/KG TOOLS")
        tabs.addTab(self._init_tab_exploit_lab(), "🧪 EXPLOIT LAB")
        return tabs

    def _init_view_service(self) -> QWidget:
        tabs = QTabWidget()
        tabs.addTab(self._init_tab_rf_lab(), "📶 RF / NETWORK")
        tabs.addTab(self._init_tab_partitions(), "📦 PARTITIONS")
        tabs.addTab(self._init_tab_chipsets(), "⚙️ CHIPSETS")
        tabs.addTab(self._init_tab_repair(), "🔧 TOOLS")
        return tabs

    def _init_view_resources(self) -> QWidget:
        tabs = QTabWidget()
        tabs.addTab(self._init_tab_mdm_qr(), "📱 QR GEN")
        tabs.addTab(self._init_tab_payloads(), "💉 PAYLOADS")
        tabs.addTab(self._init_tab_schematics(), "🛠️ SCHEMATICS")
        tabs.addTab(self._init_tab_service_diag(), "🔧 DRIVER DOCTOR")
        tabs.addTab(self._init_tab_logs(), "📜 FULL LOGS")
        return tabs

    def _init_tab_payloads(self) -> QWidget:
        widget = QWidget(); layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("STORAGE PAYLOAD INJECTOR"))
        self.combo_payloads = QComboBox(); layout.addWidget(self.combo_payloads)
        self.edit_target_part = QTextEdit(); self.edit_target_part.setFixedHeight(30); self.edit_target_part.setPlaceholderText("Target Partition (e.g. PARAM)"); layout.addWidget(self.edit_target_part)
        self.btn_inject = ModernButton("💉 INJECT SELECTED PAYLOAD", dangerous=True)
        self.btn_inject.clicked.connect(self._run_payload_injection)
        layout.addWidget(self.btn_inject)
        layout.addStretch(); self._refresh_payloads(); return widget

    # --- TAB IMPLEMENTATIONS ---

    def _init_tab_home(self) -> QWidget:
        widget = QWidget(); layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter); layout.setSpacing(20)
        lbl = QLabel("SELECT DEVICE OPERATION")
        lbl.setStyleSheet("font-size: 24px; color: #0078D4; font-weight: bold;")
        layout.addWidget(lbl)
        self.btn_frp_auto = ModernButton("🔓 SMART FRP BYPASS (ALL MODES)", primary=True)
        self.btn_frp_auto.setFixedWidth(500)
        self.btn_frp_auto.clicked.connect(self._run_frp_bypass); layout.addWidget(self.btn_frp_auto)
        self.btn_kg_auto = ModernButton("🔑 AUTO KG/MDM REMOVAL", primary=True)
        self.btn_kg_auto.setFixedWidth(500)
        self.btn_kg_auto.clicked.connect(self._run_mdm_bypass); layout.addWidget(self.btn_kg_auto)
        return widget

    def _init_tab_flash(self) -> QWidget:
        widget = QWidget(); layout = QVBoxLayout(widget)
        lbl = QLabel("SAMSUNG ODIN / MULTI-FLASH"); lbl.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(lbl)
        self.flash_files = {}
        group = QFrame(); group.setStyleSheet("background: #252525; border-radius: 5px; padding: 15px;")
        glay = QGridLayout(group)
        slots = ["BL", "AP", "CP", "CSC", "USERDATA"]
        for i, s in enumerate(slots):
            glay.addWidget(QLabel(f"{s}:"), i, 0)
            btn_pick = ModernButton(f"Select {s}..."); btn_pick.setFixedWidth(400)
            btn_pick.clicked.connect(lambda _, x=s: self._pick_flash_file(x))
            glay.addWidget(btn_pick, i, 1); self.flash_files[s] = btn_pick
        layout.addWidget(group)
        self.btn_flash = ModernButton("💾 START FLASHING", primary=True)
        self.btn_flash.clicked.connect(self._run_flash); layout.addWidget(self.btn_flash)
        layout.addStretch(); return widget

    def _init_tab_cloud(self) -> QWidget:
        widget = QWidget(); layout = QVBoxLayout(widget); layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl = QLabel("ONE-CLICK SMART AUTO-REPAIR"); lbl.setStyleSheet("font-size: 24px; color: #0078D4; font-weight: bold;")
        layout.addWidget(lbl)
        info_box = QFrame(); info_box.setStyleSheet("background: #252525; border-radius: 8px; padding: 20px;")
        info_layout = QVBoxLayout(info_box)
        info_layout.addWidget(QLabel("1. Detect Model and Bit Version"))
        info_layout.addWidget(QLabel("2. Find compatible Firmware (Oldest Patch/Same Bit)"))
        info_layout.addWidget(QLabel("3. Download and Unzip Automatically"))
        info_layout.addWidget(QLabel("4. Flash Device via Download Mode"))
        layout.addWidget(info_box)
        
        self.check_smart_bridge = QCheckBox("Enable Smart Bridge (Safe Downgrade Logic)")
        self.check_smart_bridge.setStyleSheet("color: #0078D4; font-weight: bold;")
        layout.addWidget(self.check_smart_bridge)
        
        self.btn_auto_repair = ModernButton("🚀 START AUTO-DETECT & REPAIR", primary=True)
        self.btn_auto_repair.setFixedWidth(500)
        self.btn_auto_repair.clicked.connect(self._run_auto_repair); layout.addWidget(self.btn_auto_repair)
        layout.addStretch(); return widget

    def _init_tab_hybrid(self) -> QWidget:
        widget = QWidget(); layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("HYBRID FIRMWARE ENGINE"))
        info = QLabel("Combines Combination Kernel (for ADB) with Stock Firmware."); info.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(info)
        self.btn_hybrid_gen = ModernButton("🏗️ GENERATE HYBRID FIRMWARE", primary=True)
        self.btn_hybrid_gen.clicked.connect(self._run_hybrid_engine); layout.addWidget(self.btn_hybrid_gen)
        layout.addStretch(); return widget

    def _init_tab_unlock(self) -> QWidget:
        widget = QWidget(); layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("UNLOCK & SECURITY REMOVAL"))
        self.btn_frp_download = ModernButton("🔓 REMOVE FRP (DOWNLOAD MODE)")
        self.btn_frp_download.clicked.connect(self._run_frp_bypass)
        layout.addWidget(self.btn_frp_download)
        
        self.btn_frp_mtp = ModernButton("🚀 REMOVE FRP (MTP #0*#)")
        self.btn_frp_mtp.clicked.connect(self._run_frp_bypass)
        layout.addWidget(self.btn_frp_mtp)
        
        self.btn_kg_lock = ModernButton("🔑 REMOVE KG LOCK (MDM)", dangerous=True)
        self.btn_kg_lock.clicked.connect(self._run_mdm_bypass)
        layout.addWidget(self.btn_kg_lock)
        
        self.btn_ultimate_mdm = ModernButton("🚀 ULTIMATE MDM (GHOST PIT BYPASS)", dangerous=True)
        self.btn_ultimate_mdm.setStyleSheet("background: #FF0000; font-weight: bold; border: 2px solid #FFF;")
        self.btn_ultimate_mdm.clicked.connect(self._run_ghost_pit_exploit)
        layout.addWidget(self.btn_ultimate_mdm)
        
        self.btn_bl_unlock = ModernButton("🔓 BOOTLOADER UNLOCK")
        self.btn_bl_unlock.clicked.connect(lambda: self._execute_async(self.orchestrator.run_reboot(self.current_device_id, "bootloader")))
        layout.addWidget(self.btn_bl_unlock)
        
        layout.addStretch(); return widget

    def _init_tab_rf_lab(self) -> QWidget:
        widget = QWidget(); layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("RF & SECURITY LAB (EXPERT ONLY)"))
        
        group = QFrame(); group.setStyleSheet("background: #252525; padding: 15px; border-radius: 5px;")
        glay = QGridLayout(group)
        
        # IMEI
        glay.addWidget(QLabel("NEW IMEI:"), 0, 0)
        self.edit_imei = QTextEdit(); self.edit_imei.setFixedHeight(30)
        glay.addWidget(self.edit_imei, 0, 1)
        self.btn_imei = ModernButton("📶 REPAIR IMEI"); self.btn_imei.clicked.connect(lambda: self._execute_async(self._run_repair_imei()))
        glay.addWidget(self.btn_imei, 0, 2)
        
        # CSC
        glay.addWidget(QLabel("NEW CSC:"), 1, 0)
        self.edit_csc = QTextEdit(); self.edit_csc.setFixedHeight(30)
        glay.addWidget(self.edit_csc, 1, 1)
        self.btn_csc = ModernButton("🌍 CHANGE CSC"); self.btn_csc.clicked.connect(lambda: self._execute_async(self._run_change_csc()))
        glay.addWidget(self.btn_csc, 1, 2)
        
        # Network Repair
        self.btn_rep_net = ModernButton("📡 REPAIR NETWORK", primary=True)
        self.btn_rep_net.clicked.connect(lambda: self._execute_async(self._run_repair_network()))
        glay.addWidget(self.btn_rep_net, 2, 0, 1, 3)
        
        # Patch Certificate
        self.btn_patch_cert = ModernButton("🛡️ PATCH CERTIFICATE", dangerous=True)
        self.btn_patch_cert.clicked.connect(lambda: self._execute_async(self._run_patch_cert()))
        glay.addWidget(self.btn_patch_cert, 3, 0, 1, 3)

        layout.addWidget(group)
        layout.addStretch(); return widget

    def _init_tab_partitions(self) -> QWidget:
        widget = QWidget(); layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("DEEP PARTITION MANAGER"))
        self.part_table = QTableWidget(0, 3)
        self.part_table.setHorizontalHeaderLabels(["Name", "Size", "Action"])
        self.part_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.part_table)
        btn_refresh = ModernButton("🔍 REFRESH PARTITIONS", primary=True)
        btn_refresh.clicked.connect(self._refresh_partitions); layout.addWidget(btn_refresh)
        layout.addStretch(); return widget

    def _init_tab_chipsets(self) -> QWidget:
        widget = QWidget(); layout = QVBoxLayout(widget)
        chip_tabs = QTabWidget(); chip_tabs.setStyleSheet("background: #151515;")
        
        # Qualcomm
        qcom_w = QWidget(); qlay = QVBoxLayout(qcom_w)
        qlay.addWidget(QLabel("QUALCOMM EDL (9008)"))
        self.combo_qcom_loader = QComboBox(); qlay.addWidget(self.combo_qcom_loader)
        self.btn_edl_flash = ModernButton("🛠️ EDL FLASH FIRMWARE", primary=True)
        self.btn_edl_flash.clicked.connect(self._run_edl_flash)
        qlay.addWidget(self.btn_edl_flash)
        chip_tabs.addTab(qcom_w, "Qualcomm")
        
        # MediaTek
        mtk_w = QWidget(); mlay = QVBoxLayout(mtk_w)
        mlay.addWidget(QLabel("MEDIATEK BROM (VCORE)"))
        self.btn_mtk_boot = ModernButton("🛠️ MTK BROM BOOT", primary=True)
        self.btn_mtk_boot.clicked.connect(lambda: self._execute_async(self.orchestrator.run_mtk_brom_boot(self.current_device_id, self._add_log_prog)))
        mlay.addWidget(self.btn_mtk_boot)
        chip_tabs.addTab(mtk_w, "MediaTek")
        
        # Exynos
        exy_w = QWidget(); elay = QVBoxLayout(exy_w)
        elay.addWidget(QLabel("EXYNOS EUB (FORCE BOOTING)"))
        self.combo_exy_loader = QComboBox(); elay.addWidget(self.combo_exy_loader)
        self.btn_eub_loader = ModernButton("🛠️ UPLOAD EUB LOADER", primary=True)
        self.btn_eub_loader.clicked.connect(self._run_eub_loader)
        elay.addWidget(self.btn_eub_loader)
        
        self.btn_gpu_crash = ModernButton("⚡ FORCE GPU-CRASH EXPLOIT (V2 BYPASS)", dangerous=True)
        self.btn_gpu_crash.clicked.connect(lambda: self._execute_async(self.orchestrator.run_exynos_gpu_crash(self.current_device_id, self._add_log_prog)))
        elay.addWidget(self.btn_gpu_crash)
        
        chip_tabs.addTab(exy_w, "Exynos")
        
        # Unisoc
        uni_w = QWidget(); ulay = QVBoxLayout(uni_w)
        ulay.addWidget(QLabel("UNISOC SPD (DIAG/FLASH)"))
        self.btn_uni_boot = ModernButton("🛠️ UNISOC SPD BOOT", primary=True)
        self.btn_uni_boot.clicked.connect(lambda: self._execute_async(self.orchestrator.run_unisoc_boot(self.current_device_id, self._add_log_prog)))
        ulay.addWidget(self.btn_uni_boot)
        chip_tabs.addTab(uni_w, "Unisoc")
        
        layout.addWidget(chip_tabs); layout.addStretch(); self._refresh_loaders(); return widget

    def _init_tab_exploit_lab(self) -> QWidget:
        widget = QWidget(); layout = QVBoxLayout(widget)
        lbl = QLabel("ULTIMATE EXPLOIT LAB (v10.1)"); lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #D83B01;")
        layout.addWidget(lbl)
        gp_group = QFrame(); gp_group.setStyleSheet("background: #252525; padding: 15px; border-radius: 5px;")
        gp_lay = QVBoxLayout(gp_group); gp_lay.addWidget(QLabel("1. LOKE GHOST PIT INJECTOR"))
        self.btn_ghost_pit = ModernButton("🔥 INJECT GHOST PIT", dangerous=True); self.btn_ghost_pit.clicked.connect(self._run_ghost_pit_exploit); gp_lay.addWidget(self.btn_ghost_pit); layout.addWidget(gp_group)
        sc_group = QFrame(); sc_group.setStyleSheet("background: #252525; padding: 15px; border-radius: 5px; margin-top: 10px;")
        sc_lay = QVBoxLayout(sc_group); sc_lay.addWidget(QLabel("2. PASS RESET EXPLOIT"))
        self.btn_sysui_crash = ModernButton("💥 SYSTEMUI CRASH (NO DATA)", dangerous=True); self.btn_sysui_crash.clicked.connect(self._run_sysui_crash); sc_lay.addWidget(self.btn_sysui_crash); layout.addWidget(sc_group)
        
        brute_group = QFrame(); brute_group.setStyleSheet("background: #252525; padding: 15px; border-radius: 5px; margin-top: 10px;")
        brute_lay = QVBoxLayout(brute_group); brute_lay.addWidget(QLabel("3. HANDSHAKE BRUTE-FORCE (SECURE USB BYPASS)"))
        self.btn_brute_handshake = ModernButton("⚡ BRUTE-FORCE ODIN/LOKE", dangerous=True)
        self.btn_brute_handshake.clicked.connect(lambda: self._execute_async(self.orchestrator.run_brute_handshake(self.current_device_id, self._add_log_prog)))
        brute_lay.addWidget(self.btn_brute_handshake); layout.addWidget(brute_group)

        layout.addStretch(); return widget

    def _init_tab_repair(self) -> QWidget:
        widget = QWidget(); layout = QVBoxLayout(widget)
        
        self.btn_fix_brick = ModernButton("🔧 FIX SOFT-BRICK")
        self.btn_fix_brick.clicked.connect(lambda: self._execute_async(self.orchestrator.run_auto_repair(self.current_device_id, self._add_log_prog)))
        layout.addWidget(self.btn_fix_brick)
        
        group_sn = QFrame(); group_sn.setStyleSheet("background: #252525; padding: 10px; border-radius: 5px;")
        glay_sn = QHBoxLayout(group_sn)
        glay_sn.addWidget(QLabel("NEW S/N:"))
        self.edit_sn = QTextEdit(); self.edit_sn.setFixedHeight(30)
        glay_sn.addWidget(self.edit_sn)
        self.btn_rep_sn = ModernButton("🆔 REPAIR S/N")
        self.btn_rep_sn.clicked.connect(lambda: self._execute_async(self._run_repair_sn()))
        glay_sn.addWidget(self.btn_rep_sn)
        layout.addWidget(group_sn)
        
        self.btn_back_efs = ModernButton("🛡️ BACKUP EFS PARTITION", primary=True)
        self.btn_back_efs.clicked.connect(lambda: self._execute_async(self._run_backup_efs()))
        layout.addWidget(self.btn_back_efs)
        
        self.btn_rep_imei_tool = ModernButton("📶 REPAIR IMEI (RF LAB)", dangerous=True)
        self.btn_rep_imei_tool.clicked.connect(lambda: self.sidebar.buttons[3].click()) 
        layout.addWidget(self.btn_rep_imei_tool)
        
        layout.addStretch(); return widget

    def _init_tab_mdm_qr(self) -> QWidget:
        widget = QWidget(); layout = QVBoxLayout(widget); layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_qr_img = QLabel(); self.lbl_qr_img.setFixedSize(250, 250); self.lbl_qr_img.setStyleSheet("background: #FFF;"); layout.addWidget(self.lbl_qr_img)
        self.qr_text = QTextEdit(); self.qr_text.setFixedHeight(80); self.qr_text.setReadOnly(True); layout.addWidget(self.qr_text)
        btn_gen = ModernButton("📲 GENERATE QR", primary=True); btn_gen.clicked.connect(self._run_qr_gen); layout.addWidget(btn_gen); layout.addStretch(); return widget

    def _init_tab_schematics(self) -> QWidget:
        widget = QWidget(); layout = QVBoxLayout(widget)
        txt = QTextEdit(); txt.setReadOnly(True)
        txt.setStyleSheet("background:#000; color:#00FF41; font-family:'Consolas', monospace;")
        content = """[ EXYNOS TEST POINT - EUB MODE ]
1. Disconnect Battery
2. Short CLK to GND (Check hardware guide)
3. Insert USB Cable
4. Device should show as 'Exynos USB Booting'

[ QUALCOMM TEST POINT - EDL MODE ]
1. Disconnect Battery
2. Short EDL Test Points (Near CPU/UFS)
3. Insert USB Cable
4. Device should show as 'Qualcomm HS-USB QDLoader 9008'

[ MTK BROM MODE ]
1. Power Off Device
2. Hold VOL+ and VOL- (or one of them)
3. Insert USB Cable
4. Device should show as 'MediaTek USB Port'
"""
        txt.setText(content)
        layout.addWidget(txt); return widget

    def _init_tab_service_diag(self) -> QWidget:
        widget = QWidget(); layout = QVBoxLayout(widget); layout.addWidget(QLabel("DIAGNOSTICS"))
        self.btn_dr_doctor = ModernButton("🔧 RUN DRIVER DOCTOR", primary=True); self.btn_dr_doctor.clicked.connect(self._run_driver_doctor); layout.addWidget(self.btn_dr_doctor); layout.addStretch(); return widget

    def _init_tab_logs(self) -> QWidget:
        widget = QWidget(); layout = QVBoxLayout(widget)
        self.log_area = QTextEdit(); self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet("background: #000; color: #00FF41; font-family: 'Consolas', monospace;")
        layout.addWidget(self.log_area)
        
        btn_lay = QHBoxLayout()
        self.btn_view_startup = ModernButton("📜 VIEW STARTUP LOG")
        self.btn_view_startup.clicked.connect(self._view_startup_log)
        btn_lay.addWidget(self.btn_view_startup)
        layout.addLayout(btn_lay)
        
        return widget

    def _view_startup_log(self):
        try:
            with open("samsung_monster_startup.log", "r") as f:
                self.log_area.setPlainText(f.read())
        except:
            self._add_log("❌ Startup log not found.")

    # --- ACTIONS & LOGIC ---

    def _pick_flash_file(self, slot):
        path, _ = QFileDialog.getOpenFileName(self, f"Select {slot} File", "", "Samsung Flash Files (*.tar *.md5 *.img)")
        if path:
            self.flash_files[slot].setText(os.path.basename(path))
            self.flash_files[slot].setToolTip(path)

    async def _run_read_info(self):
        if not self.current_device_id: return
        self._add_log("🔍 Reading Deep Device Info...")
        info = await self.orchestrator.get_device_full_info(self.current_device_id)
        if info:
            model = info.get("model", "UNKNOWN"); bit = info.get("bit", "-")
            region = info.get("region", "---"); version = info.get("version", "---")
            variant = await self.orchestrator.identify_variant(self.current_device_id, self._add_log_prog)
            if variant in {"Unknown", "Standard Device"} and info.get("product"):
                variant = info.get("product")
            self.lbl_det_model.setText(f"Model: {model}"); self.lbl_det_bit.setText(f"Bit: {bit}")
            self.lbl_det_region.setText(f"Region: {region}"); self.lbl_det_version.setText(f"Version: {version}")
            self.lbl_det_variant.setText(f"Variant: {variant}")
            self.status_card.update_status(True, f"DEVICE: {model}", f"Model: {model} | Bit: {bit} | Mode: {info.get('mode', '---')}", f"Serial: {self.current_device_id}")
            self._add_log(f"✅ Device Identified: {model} (Bit {bit})")

    async def _run_repair_imei(self):
        if not self.current_device_id: return
        imei = self.edit_imei.toPlainText().strip()
        if not imei: return
        self._add_log(f"📶 Starting IMEI Repair: {imei}")
        protocol = await self.orchestrator.get_protocol(self.current_device_id)
        if protocol:
            async with protocol:
                from operations.samsung_ops import SamsungOperations
                ops = SamsungOperations(protocol)
                res = await ops.repair_imei(imei)
                self._add_log("✅ IMEI Repair Completed" if res else "❌ IMEI Repair Failed")

    async def _run_change_csc(self):
        if not self.current_device_id: return
        csc = self.edit_csc.toPlainText().strip()
        if not csc: return
        self._add_log(f"🌍 Starting CSC Change: {csc}")
        protocol = await self.orchestrator.get_protocol(self.current_device_id)
        if protocol:
            async with protocol:
                from operations.samsung_ops import SamsungOperations
                ops = SamsungOperations(protocol)
                res = await ops.change_csc(csc)
                self._add_log("✅ CSC Change Completed" if res else "❌ CSC Change Failed")

    async def _run_repair_network(self):
        if not self.current_device_id: return
        self._add_log("📡 Starting Network/RF Repair...")
        res = await self.orchestrator.repair_network(self.current_device_id, self._add_log_prog)
        self._add_log("✅ Network Repaired" if res else "❌ Network Repair Failed")

    async def _run_patch_cert(self):
        if not self.current_device_id: return
        path, _ = QFileDialog.getOpenFileName(self, "Select Certificate File", "", "Certificate Files (*.cert *.bin *.sig)")
        if not path: return
        with open(path, "rb") as f: cert_data = f.read()
        self._add_log(f"🛡️ Patching Certificate: {os.path.basename(path)}...")
        res = await self.orchestrator.patch_certificate(self.current_device_id, cert_data, self._add_log_prog)
        self._add_log("✅ Certificate Patched" if res else "❌ Certificate Patch Failed")

    async def _run_repair_sn(self):
        if not self.current_device_id: return
        sn = self.edit_sn.toPlainText().strip()
        if not sn: return
        self._add_log(f"🆔 Repairing S/N: {sn}...")
        res = await self.orchestrator.repair_serial(self.current_device_id, sn, self._add_log_prog)
        self._add_log("✅ S/N Repaired" if res else "❌ S/N Repair Failed")

    async def _run_backup_efs(self):
        if not self.current_device_id: return
        path, _ = QFileDialog.getSaveFileName(self, "Save EFS Backup", "EFS_Backup.bin", "Binary Files (*.bin)")
        if not path: return
        self._add_log("🛡️ Backing up EFS partition...")
        res = await self.orchestrator.backup_efs(self.current_device_id, path, self._add_log_prog)
        self._add_log(f"✅ EFS saved to: {path}" if res else "❌ EFS Backup Failed")

    def _connect_signals(self):
        self.emitter.log_signal.connect(self._add_log)
        self.emitter.progress_signal.connect(self.progress_bar.setValue)
        self.emitter.device_event.connect(self._handle_device_event)
        self.orchestrator.device_manager.event_callback = lambda e, d: self.emitter.device_event.emit(e, d)
        # Immediate scan so already-connected devices populate the panel on startup.
        self.orchestrator.device_manager.scan_now()

    def _add_log(self, msg: str):
        t = time.strftime('%H:%M:%S')
        formatted = f"[{t}] {msg}"
        if hasattr(self, 'mini_log') and self.mini_log: self.mini_log.append(formatted)
        if hasattr(self, 'log_area') and self.log_area: self.log_area.append(formatted)

    async def _run_edl_flash(self):
        if not self.current_device_id: return
        loader = self.combo_qcom_loader.currentText()
        if not loader or loader == "No loaders":
            self._add_log("❌ Error: No Qualcomm loader selected.")
            return
        
        from utils.loader_manager import LoaderManager
        loader_path = LoaderManager.get_loader_path("qualcomm", loader)
        
        flash_plan = {} # No GUI yet for EDL multi-file, let's pick one
        path, _ = QFileDialog.getOpenFileName(self, "Select Image to Flash via EDL", "", "Binary/Image Files (*.bin *.img *.xml)")
        if not path: return
        flash_plan["PROGRAM"] = path # Generic label for EDL firehose
        
        self._add_log(f"🛠️ Starting EDL Flash with loader: {loader}...")
        res = await self.orchestrator.run_edl_flash(self.current_device_id, loader_path, flash_plan, self._add_log_prog)
        self._add_log("✅ EDL Flash Completed" if res else "❌ EDL Flash Failed")

    async def _run_eub_loader(self):
        if not self.current_device_id: return
        loader = self.combo_exy_loader.currentText()
        if not loader or loader == "No loaders":
            self._add_log("❌ Error: No Exynos loader selected.")
            return
        
        from utils.loader_manager import LoaderManager
        loader_path = LoaderManager.get_loader_path("exynos", loader)
        
        self._add_log(f"🛠️ Uploading EUB Loader: {loader}...")
        res = await self.orchestrator.run_eub_loader(self.current_device_id, loader_path, self._add_log_prog)
        self._add_log("✅ EUB Loader Executed" if res else "❌ EUB Loader Failed")

    async def _run_deep_diagnose(self):
        if not self.current_device_id: return
        self._add_log("🩺 Starting Deep Hardware Diagnosis...")
        info = await self.orchestrator.run_deep_diagnose(self.current_device_id, self._add_log_prog)
        if "error" not in info:
            self._add_log(f"✅ Diagnosis Results: {info['manufacturer']} {info['product']}")
            self._add_log(f"📍 Serial: {info['serial']} | ID: {info['vendor_id']}:{info['product_id']}")
        else:
            self._add_log(f"❌ Diagnostic failed: {info['error']}")

    def _update_ui_state(self, mode: ConnectionMode):
        """Enable/Disable features based on current connection mode (Modified for Live GUI)"""
        # Manter botões habilitados para exploração, mas validar no clique.
        pass

    def _handle_device_event(self, event: str, dev):
        if event in ["CONNECTED", "MODE_CHANGED"]:
            self.current_device_id = dev.serial
            self.status_card.update_status(True, f"DEVICE: {dev.mode.value}", f"Serial: {dev.serial}")
            self._add_log(f"🟢 Device {event}: {dev.serial} ({dev.mode.value})")
            self._update_ui_state(dev.mode)
            self._execute_async(self._run_read_info()) 
        elif event == "DISCONNECTED":
            self.current_device_id = None
            self.status_card.update_status(False)
            self._add_log("🔴 Device Disconnected")
            self._update_ui_state(ConnectionMode.UNKNOWN)

    def _execute_async(self, coro):
        async def wrapper():
            try: await coro
            except Exception as e: self.emitter.log_signal.emit(f"❌ Error: {e}")
        asyncio.run_coroutine_threadsafe(wrapper(), self.loop)

    def _run_frp_bypass(self):
        if not self.current_device_id: return
        self._add_log("🚀 Starting FRP Bypass...")
        self._execute_async(self.orchestrator.run_frp_bypass(self.current_device_id, self._add_log_prog))

    def _run_mdm_bypass(self):
        if not self.current_device_id: return
        self._add_log("🔥 Starting MDM Bypass...")
        self._execute_async(self.orchestrator.run_mdm_bypass(self.current_device_id, self._add_log_prog))

    def _run_auto_repair(self):
        if not self.current_device_id: return
        bridge = self.check_smart_bridge.isChecked()
        self._add_log(f"🚀 Starting Auto-Repair (Smart Bridge: {'ON' if bridge else 'OFF'})...")
        # I'll need to update orchestrator.run_auto_repair to accept bridge parameter
        self._execute_async(self.orchestrator.run_auto_repair(self.current_device_id, self._add_log_prog, bridge_mode=bridge))

    def _run_ghost_pit_exploit(self):
        if not self.current_device_id: return
        self._add_log("🔥 Initiating Ghost PIT Injection Exploit...")
        self._execute_async(self.orchestrator.run_ghost_pit_exploit(self.current_device_id, self._add_log_prog))

    def _run_hybrid_engine(self):
        self._add_log("🏗️ Hybrid Engine requested.")
        self._execute_async(self.orchestrator.run_hybrid_engine_create("comb.tar", "stock.tar", "hybrid.tar", self._add_log_prog))

    def _run_sysui_crash(self):
        if not self.current_device_id: return
        self._add_log("💥 Triggering SystemUI Crash Exploit...")
        self._execute_async(self.orchestrator.run_sysui_crash_exploit(self.current_device_id, self._add_log_prog))

    def _run_flash(self):
        if not self.current_device_id:
            self._add_log("❌ Error: No device connected.")
            return
            
        flash_plan = {}
        for slot, btn in self.flash_files.items():
            path = btn.toolTip()
            if path and os.path.exists(path):
                flash_plan[slot] = path
        
        if not flash_plan:
            self._add_log("❌ Error: No flash files selected.")
            return
            
        self._add_log(f"💾 Starting Odin Flash with {len(flash_plan)} files...")
        self._execute_async(self.orchestrator.run_flash_firmware(self.current_device_id, flash_plan, self._add_log_prog))

    def _run_qr_gen(self):
        from utils.qr_generator import MDMQRGenerator
        path = "provisioning_qr.png"
        if MDMQRGenerator.save_qr_image(path):
            self.lbl_qr_img.setPixmap(QPixmap(path).scaled(250, 250, Qt.AspectRatioMode.KeepAspectRatio))
            self.qr_text.setText(MDMQRGenerator.generate_monster_bypass_string())

    def _refresh_loaders(self):
        try:
            from utils.loader_manager import LoaderManager
            self.combo_qcom_loader.clear()
            self.combo_qcom_loader.addItems(LoaderManager.list_loaders("qualcomm") or ["No loaders"])
            self.combo_exy_loader.clear()
            self.combo_exy_loader.addItems(LoaderManager.list_loaders("exynos") or ["No loaders"])
        except: pass

    def _refresh_payloads(self):
        try:
            payloads = self.orchestrator.list_payloads()
            self.combo_payloads.clear()
            self.combo_payloads.addItems(payloads or ["No payloads in storage/payloads"])
        except: pass

    async def _run_payload_injection(self):
        if not self.current_device_id: return
        payload = self.combo_payloads.currentText()
        partition = self.edit_target_part.toPlainText().strip()
        if not partition or "No payloads" in payload: return
        
        self._add_log(f"💉 Initiating Payload Injection: {payload} -> {partition}")
        res = await self.orchestrator.inject_payload(self.current_device_id, payload, partition, self._add_log_prog)
        self._add_log("✅ Injection Successful" if res else "❌ Injection Failed")

    async def _run_refresh_partitions(self):
        if not self.current_device_id: return
        self._add_log("🔍 Scanning Device Partitions...")
        partitions = await self.orchestrator.list_partitions(self.current_device_id, self._add_log_prog)
        
        self.part_table.setRowCount(0)
        for p in partitions:
            row = self.part_table.rowCount()
            self.part_table.insertRow(row)
            self.part_table.setItem(row, 0, QTableWidgetItem(p.name))
            size_mb = p.size // (1024 * 1024)
            self.part_table.setItem(row, 1, QTableWidgetItem(f"{size_mb} MB"))
            
            # Action Buttons
            btn_container = QWidget()
            btn_lay = QHBoxLayout(btn_container)
            btn_lay.setContentsMargins(2, 2, 2, 2)
            
            btn_read = QPushButton("Read")
            btn_read.setStyleSheet("background: #0078D4; font-size: 10px; height: 20px;")
            btn_read.clicked.connect(lambda _, n=p.name: self._execute_async(self._run_read_partition(n)))
            btn_lay.addWidget(btn_read)
            
            btn_erase = QPushButton("Erase")
            btn_erase.setStyleSheet("background: #D83B01; font-size: 10px; height: 20px;")
            btn_erase.clicked.connect(lambda _, n=p.name: self._execute_async(self._run_erase_partition(n)))
            btn_lay.addWidget(btn_erase)
            
            self.part_table.setCellWidget(row, 2, btn_container)
        
        self._add_log(f"✅ Found {len(partitions)} partitions.")

    async def _run_read_partition(self, name):
        path, _ = QFileDialog.getSaveFileName(self, f"Save {name} Partition", f"{name}.bin", "Binary Files (*.bin)")
        if not path: return
        self._add_log(f"📖 Reading partition: {name}...")
        res = await self.orchestrator.read_partition(self.current_device_id, name, path, self._add_log_prog)
        self._add_log(f"✅ {name} backup saved." if res else f"❌ Failed to read {name}.")

    async def _run_erase_partition(self, name):
        self._add_log(f"🧹 Erasing partition: {name}...")
        res = await self.orchestrator.erase_partition(self.current_device_id, name, self._add_log_prog)
        self._add_log(f"✅ {name} erased." if res else f"❌ Failed to erase {name}.")

    def _refresh_partitions(self):
        self._execute_async(self._run_refresh_partitions())

    def _run_driver_doctor(self):
        from utils.driver_doctor import DriverDoctor
        self._add_log("🩺 Running System Driver Health Check...")
        issues = DriverDoctor.diagnose()
        if not issues:
            self._add_log("✅ All systems go! No driver issues found.")
            return
        
        for i in issues:
            msg = f"⚠️ ISSUE: {i['issue']}"
            if i.get('fixable'):
                msg += " (Can be fixed via terminal)"
            self._add_log(msg)
            if i.get("fixable") and i.get("id"):
                fixed = DriverDoctor.auto_fix(i["id"])
                self._add_log("🛠️ Auto-fix applied." if fixed else "❌ Auto-fix failed.")
    def _add_log_prog(self, data):
        if isinstance(data, dict):
            msg = data.get("stage", "")
            pct = data.get("percent", 0)
            if msg: self._add_log(msg)
            self.emitter.progress_signal.emit(pct)
        else: self._add_log(str(data))
