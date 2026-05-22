"""排泄 - 日志轮替，防止日志过大"""
from skeleton.base_organ import BaseOrgan
from pathlib import Path

class LogRotator(BaseOrgan):
    def __init__(self, log_dir: Path, max_size_mb: int = 10):
        super().__init__("log_rotator")
        self.log_dir = Path(log_dir)
        self.max_size = max_size_mb * 1024 * 1024

    def rotate(self):
        """如果日志超过限制，进行轮替"""
        for log_file in self.log_dir.glob("*.log"):
            if log_file.stat().st_size > self.max_size:
                backup = log_file.with_suffix(".log.old")
                if backup.exists():
                    backup.unlink()
                log_file.rename(backup)
                log_file.touch()

    def status(self) -> dict:
        return {"name": self.name, "alive": self.is_alive()}
