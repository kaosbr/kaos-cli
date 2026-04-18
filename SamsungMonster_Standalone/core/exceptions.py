class SamsungMonsterError(Exception):
    """Base exception for all project errors"""
    def __init__(self, message: str, code: str = "E000", solution: str = "Check logs"):
        self.message = message
        self.code = code
        self.solution = solution
        super().__init__(f"[{code}] {message} -> Hint: {solution}")

class DeviceError(SamsungMonsterError):
    def __init__(self, message: str):
        super().__init__(message, code="E100", solution="Check USB cable and port")

class ProtocolError(SamsungMonsterError):
    def __init__(self, message: str):
        super().__init__(message, code="E200", solution="Ensure correct mode (EDL/BROM/Odin)")

class ExploitError(SamsungMonsterError):
    """Raised when an exploit fails to execute or is patched"""
    def __init__(self, message: str):
        super().__init__(message, code="E300")

class SecurityError(SamsungMonsterError):
    """Raised during integrity check failures"""
    def __init__(self, message: str):
        super().__init__(message, code="E400")
