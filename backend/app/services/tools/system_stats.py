import psutil
import shutil

def get_system_diagnostics() -> str:
    """Retrieves current CPU usage, RAM availability, and disk space of the host machine."""
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = shutil.disk_usage("/")
    
    return (
        f"System Status: CPU Usage: {cpu_percent}%, "
        f"Available RAM: {round(memory.available / (1024**3), 2)} GB, "
        f"Free Disk Space: {round(disk.free / (1024**3), 2)} GB."
    )