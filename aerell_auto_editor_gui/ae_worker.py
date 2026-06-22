import sys
import subprocess
from PySide6.QtCore import QThread, Signal

class AEWorker(QThread):
    line_output = Signal(str)
    finished = Signal(int)  # returncode

    def __init__(self, args: list[str]):
        super().__init__()
        self._args = args

    def run(self):
        try:
            proc = subprocess.Popen(
                [sys.executable, '-m', 'auto_editor'] + self._args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
            )
            for line in proc.stdout:
                self.line_output.emit(line.rstrip('\n'))
            proc.wait()
            self.finished.emit(proc.returncode)
        except Exception as e:
            self.line_output.emit(f'[ERROR] {e}')
            self.finished.emit(1)
