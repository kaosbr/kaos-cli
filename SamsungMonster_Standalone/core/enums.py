from enum import Enum

class ConnectionMode(Enum):
    UNKNOWN = "UNKNOWN"
    ADB = "ADB"
    FASTBOOT = "FASTBOOT"
    ODIN = "ODIN"
    EUB = "EUB"
    MODEM = "MODEM"
    BROM = "BROM"
    EDL = "EDL"
    SPD = "SPD"
    RECOVERY = "RECOVERY"
    NORMAL = "NORMAL"
