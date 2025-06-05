# system_monitor.py
# Description: Modern Python script to monitor and display CPU, memory, disk I/O,
#              and network I/O via Discord Rich Presence.
# Requires: psutil (pip install psutil), pypresence (pip install pypresence)

import psutil
import time
import argparse
from typing import Optional, Dict, Any
import random

try:
    from pypresence import Presence, exceptions as pypresence_exceptions
    PYPRESENCE_AVAILABLE = True
except ImportError:
    PYPRESENCE_AVAILABLE = False
    print("Warning: 'pypresence' library not found. Discord RPC functionality will be disabled.")
    print("Install it with: pip install pypresence")

DEFAULT_RPC_UPDATE_INTERVAL = 10
DEFAULT_DISCORD_CLIENT_ID = "1380200369144987760"

RPC: Optional[Presence] = None
last_rpc_update_time = 0
initial_script_start_time = time.time()

def parse_args():
    parser = argparse.ArgumentParser(description="System Monitor with Discord Rich Presence")
    parser.add_argument("--rpc-update-interval", type=int, default=DEFAULT_RPC_UPDATE_INTERVAL, help="Discord RPC update interval (seconds)")
    parser.add_argument("--discord-client-id", default=DEFAULT_DISCORD_CLIENT_ID, help="Discord Application Client ID")
    return parser.parse_args()

def get_cpu_usage(sample_interval: int = 1) -> Optional[Dict[str, Any]]:
    try:
        overall = psutil.cpu_percent(interval=sample_interval)
        per_core = psutil.cpu_percent(interval=None, percpu=True)
        return {"overall": overall, "cores": per_core}
    except Exception:
        return None

def get_memory_usage() -> Optional[Dict[str, float]]:
    try:
        mem = psutil.virtual_memory()
        return {
            "total": mem.total,
            "used": mem.used,
            "percent": mem.percent
        }
    except Exception:
        return None

def get_disk_io() -> Optional[Dict[str, float]]:
    try:
        io = psutil.disk_io_counters()
        if io:
            return {
                "read": io.read_bytes,
                "write": io.write_bytes
            }
        return None
    except Exception:
        return None

def get_network_io() -> Optional[Dict[str, float]]:
    try:
        net = psutil.net_io_counters()
        if net:
            return {
                "sent": net.bytes_sent,
                "recv": net.bytes_recv
            }
        return None
    except Exception:
        return None

def human_readable(num: float, suffix: str = "B") -> str:
    for unit in ["", "K", "M", "G", "T", "P"]:
        if abs(num) < 1024.0:
            return f"{num:.1f} {unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f} P{suffix}"

def get_presence_variants(cpu, mem, disk, net):
    variants = []
    # CPU & RAM
    variants.append((
        f"CPU: {cpu['overall']:.1f}%",
        f"RAM: {mem['percent']:.1f}% ({human_readable(mem['used'])}/{human_readable(mem['total'])})"
    ))
    # Disk & Net
    if disk and net:
        variants.append((
            f"Disk R/W: {human_readable(disk['read'])}/{human_readable(disk['write'])}",
            f"Net S/R: {human_readable(net['sent'])}/{human_readable(net['recv'])}"
        ))
    # CPU & Disk
    if disk:
        variants.append((
            f"CPU: {cpu['overall']:.1f}%",
            f"Disk R/W: {human_readable(disk['read'])}/{human_readable(disk['write'])}"
        ))
    # RAM & Net
    if net:
        variants.append((
            f"RAM: {mem['percent']:.1f}% ({human_readable(mem['used'])}/{human_readable(mem['total'])})",
            f"Net S/R: {human_readable(net['sent'])}/{human_readable(net['recv'])}"
        ))
    return variants

def initialize_rpc(client_id: str) -> bool:
    global RPC
    if not PYPRESENCE_AVAILABLE or client_id == "YOUR_CLIENT_ID_HERE":
        return False
    RPC = Presence(client_id)
    try:
        RPC.connect()
        return True
    except Exception:
        RPC = None
        return False

def update_discord_presence(
    cpu: Dict[str, Any],
    mem: Dict[str, float],
    disk: Optional[Dict[str, float]] = None,
    net: Optional[Dict[str, float]] = None
) -> None:
    global RPC
    if RPC is None or not PYPRESENCE_AVAILABLE:
        return
    try:
        variants = get_presence_variants(cpu, mem, disk, net)
        details, state = random.choice(variants)
        RPC.update(
            details=details,
            state=state,
            large_image="system_monitor_logo",
            large_text="System Performance Monitor",
            small_image="python_icon",
            small_text="Monitoring System...",
            start=int(initial_script_start_time)
        )
    except Exception:
        RPC = None

def close_rpc() -> None:
    global RPC
    if RPC and PYPRESENCE_AVAILABLE:
        try:
            RPC.close()
        except Exception:
            pass
    RPC = None

def main():
    global RPC, last_rpc_update_time, initial_script_start_time

    args = parse_args()
    rpc_update_interval = args.rpc_update_interval
    discord_client_id = args.discord_client_id

    if not (PYPRESENCE_AVAILABLE and discord_client_id != "YOUR_CLIENT_ID_HERE"):
        print("Discord RPC not available or client ID not set.")
        return

    initial_script_start_time = time.time()
    last_rpc_update_time = 0

    try:
        while True:
            current_time = time.time()
            cpu_data = get_cpu_usage()
            mem_data = get_memory_usage()
            disk_data = get_disk_io()
            net_data = get_network_io()

            if RPC is None:
                initialize_rpc(discord_client_id)
            if RPC and (current_time - last_rpc_update_time >= rpc_update_interval):
                if cpu_data and mem_data:
                    update_discord_presence(
                        cpu_data,
                        mem_data,
                        disk_data,
                        net_data
                    )
                    last_rpc_update_time = current_time

            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        if PYPRESENCE_AVAILABLE:
            close_rpc()

if __name__ == "__main__":
    try:
        import psutil
    except ImportError:
        print("Error: The 'psutil' library is not installed.")
        print("Please install it by running: pip install psutil")
        exit(1)
    main()