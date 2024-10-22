import torch
from PySide6.QtCore import Signal, QObject, QTimer

import pcleaner.helpers as hp


class MemoryWatcher(QObject):
    # Monitor system memory usage to warn of impending OOM errors.
    oom_warning = Signal(str)
    oom_relaxed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_memory)

    def start(self):
        # Start the timer to check memory every second (1000 ms)
        self.timer.start(2000)

    def stop(self):
        # Stop the timer
        self.timer.stop()

    def check_memory(self):
        # Monitor system memory (RAM)
        oom: bool = False

        # Check conditions for RAM and swap.
        if hp.sys_swap_memory_total() == 0:  # No swap available.
            if (mem := hp.sys_virtual_memory_used_percent()) >= 80:
                self.oom_warning.emit(
                    self.tr("RAM usage has reached {mem}%").format(mem=round(mem))
                )
                oom = True
        else:  # Swap is available
            if (mem := hp.sys_virtual_memory_used_percent()) >= 90:
                # self.oom_warning.emit("RAM usage has reached 100%.")
                self.oom_warning.emit(
                    self.tr("RAM usage has reached {mem}%").format(mem=round(mem))
                )
                oom = True

        # Monitor VRAM if torch is available and GPU is detected.
        if torch.cuda.is_available() and torch.cuda.device_count() > 0:
            vram_total = torch.cuda.get_device_properties(0).total_memory
            vram_used = torch.cuda.memory_allocated(0)
            vram_percent = (vram_used / vram_total) * 100

            if vram_percent >= 80:
                self.oom_warning.emit(
                    "VRAM usage has reached {vmem}%".format(vmem=round(vram_percent))
                )
                oom = True

        if not oom:
            self.oom_relaxed.emit()
