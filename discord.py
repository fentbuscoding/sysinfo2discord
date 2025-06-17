# system_monitor.py
# Description: Cross-platform Python script to monitor and display CPU, memory, disk I/O,
#              and network I/O via Discord Rich Presence.
# Requires: psutil (pip install psutil), pypresence (pip install pypresence)
# Compatible with: Windows, macOS, Linux

import psutil
import time
import argparse
import platform
import sys
from typing import Optional, Dict, Any
import random

try:
    from pypresence import Presence, exceptions as pypresence_exceptions
    PYPRESENCE_AVAILABLE = True
except ImportError:
    PYPRESENCE_AVAILABLE = False
    print("Warning: 'pypresence' library not found. Discord RPC functionality will be disabled.")
    if platform.system() == "Windows":
        print("Install it with: pip install pypresence")
    else:
        print("Install it with: pip install pypresence (or use a virtual environment)")

DEFAULT_RPC_UPDATE_INTERVAL = 10
DEFAULT_DISCORD_CLIENT_ID = "1380200369144987760"

# Cross-platform compatibility
CURRENT_OS = platform.system()
OS_NAME = {
    "Windows": "Windows",
    "Darwin": "macOS", 
    "Linux": "Linux"
}.get(CURRENT_OS, CURRENT_OS)

RPC: Optional[Presence] = None
last_rpc_update_time = 0
initial_script_start_time = time.time()

def parse_args():
    parser = argparse.ArgumentParser(description=f"System Monitor with Discord Rich Presence - {OS_NAME}")
    parser.add_argument("--rpc-update-interval", type=int, default=DEFAULT_RPC_UPDATE_INTERVAL, 
                       help="Discord RPC update interval (seconds)")
    parser.add_argument("--discord-client-id", default=DEFAULT_DISCORD_CLIENT_ID, 
                       help="Discord Application Client ID")
    parser.add_argument("--show-os", action="store_true", 
                       help="Show operating system in Discord presence")
    return parser.parse_args()

def get_cpu_usage(sample_interval: int = 1) -> Optional[Dict[str, Any]]:
    """Get CPU usage with cross-platform optimization"""
    try:
        # Use shorter interval on Windows for better responsiveness
        if CURRENT_OS == "Windows":
            sample_interval = min(sample_interval, 0.5)
        
        overall = psutil.cpu_percent(interval=sample_interval)
        per_core = psutil.cpu_percent(interval=None, percpu=True)
        
        # Get CPU frequency if available (varies by OS)
        freq_info = None
        try:
            freq = psutil.cpu_freq()
            if freq:
                freq_info = {
                    "current": freq.current,
                    "min": freq.min,
                    "max": freq.max
                }
        except (AttributeError, OSError):
            # Some systems don't support CPU frequency monitoring
            pass
            
        return {
            "overall": overall, 
            "cores": per_core,
            "frequency": freq_info
        }
    except Exception as e:
        print(f"Error getting CPU usage: {e}")
        return None

def get_memory_usage() -> Optional[Dict[str, float]]:
    """Get memory usage with OS-specific details"""
    try:
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        result = {
            "total": mem.total,
            "used": mem.used,
            "percent": mem.percent,
            "available": mem.available
        }
        
        # Add swap information if available
        if swap.total > 0:
            result["swap_total"] = swap.total
            result["swap_used"] = swap.used
            result["swap_percent"] = swap.percent
            
        return result
    except Exception as e:
        print(f"Error getting memory usage: {e}")
        return None

def get_disk_io() -> Optional[Dict[str, float]]:
    """Get disk I/O with cross-platform handling"""
    try:
        io = psutil.disk_io_counters()
        if io:
            result = {
                "read": io.read_bytes,
                "write": io.write_bytes,
                "read_count": io.read_count,
                "write_count": io.write_count
            }
            
            # Add read/write time if available (not available on all platforms)
            if hasattr(io, 'read_time') and hasattr(io, 'write_time'):
                result["read_time"] = io.read_time
                result["write_time"] = io.write_time
                
            return result
        return None
    except Exception as e:
        print(f"Error getting disk I/O: {e}")
        return None

def get_network_io() -> Optional[Dict[str, float]]:
    """Get network I/O with cross-platform handling"""
    try:
        net = psutil.net_io_counters()
        if net:
            return {
                "sent": net.bytes_sent,
                "recv": net.bytes_recv,
                "packets_sent": net.packets_sent,
                "packets_recv": net.packets_recv,
                "errors_in": net.errin,
                "errors_out": net.errout,
                "drops_in": net.dropin,
                "drops_out": net.dropout
            }
        return None
    except Exception as e:
        print(f"Error getting network I/O: {e}")
        return None

def get_system_info() -> Dict[str, str]:
    """Get basic system information"""
    try:
        return {
            "os": OS_NAME,
            "platform": platform.platform(),
            "architecture": platform.architecture()[0],
            "processor": platform.processor() or "Unknown",
            "hostname": platform.node(),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        }
    except Exception:
        return {"os": OS_NAME}

def human_readable(num: float, suffix: str = "B") -> str:
    """Convert bytes to human readable format"""
    if num is None:
        return "N/A"
    
    for unit in ["", "K", "M", "G", "T", "P"]:
        if abs(num) < 1024.0:
            return f"{num:.1f} {unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f} P{suffix}"

def get_presence_variants(cpu, mem, disk, net, show_os=False):
    """Generate different presence variants with OS info option"""
    variants = []
    os_suffix = f" | {OS_NAME}" if show_os else ""
    
    # CPU & RAM
    variants.append((
        f"CPU: {cpu['overall']:.1f}%{os_suffix}",
        f"RAM: {mem['percent']:.1f}% ({human_readable(mem['used'])}/{human_readable(mem['total'])})"
    ))
    
    # Disk & Net
    if disk and net:
        variants.append((
            f"Disk R/W: {human_readable(disk['read'])}/{human_readable(disk['write'])}{os_suffix}",
            f"Net S/R: {human_readable(net['sent'])}/{human_readable(net['recv'])}"
        ))
    
    # CPU & Disk
    if disk:
        variants.append((
            f"CPU: {cpu['overall']:.1f}%{os_suffix}",
            f"Disk R/W: {human_readable(disk['read'])}/{human_readable(disk['write'])}"
        ))
    
    # RAM & Net
    if net:
        variants.append((
            f"RAM: {mem['percent']:.1f}% ({human_readable(mem['used'])}/{human_readable(mem['total'])}){os_suffix}",
            f"Net S/R: {human_readable(net['sent'])}/{human_readable(net['recv'])}"
        ))
    
    # CPU Frequency (if available)
    if cpu.get('frequency') and show_os:
        freq = cpu['frequency']
        variants.append((
            f"CPU: {cpu['overall']:.1f}% @ {freq['current']:.0f}MHz",
            f"RAM: {mem['percent']:.1f}% | {OS_NAME}"
        ))
    
    # Swap info (if available and significant)
    if mem.get('swap_total', 0) > 0 and mem.get('swap_percent', 0) > 5:
        variants.append((
            f"RAM: {mem['percent']:.1f}% | Swap: {mem['swap_percent']:.1f}%{os_suffix}",
            f"Physical: {human_readable(mem['used'])}/{human_readable(mem['total'])}"
        ))
    
    return variants

def initialize_rpc(client_id: str) -> bool:
    """Initialize Discord RPC with cross-platform error handling"""
    global RPC
    if not PYPRESENCE_AVAILABLE or client_id == "YOUR_CLIENT_ID_HERE":
        return False
    
    RPC = Presence(client_id)
    try:
        RPC.connect()
        print(f"Discord RPC connected successfully on {OS_NAME}")
        return True
    except Exception as e:
        print(f"Failed to connect to Discord RPC on {OS_NAME}: {e}")
        if CURRENT_OS == "Linux":
            print("Make sure Discord is running and try: export DISPLAY=:0")
        elif CURRENT_OS == "Darwin":
            print("Make sure Discord is running and has proper permissions")
        elif CURRENT_OS == "Windows":
            print("Make sure Discord is running as the same user")
        RPC = None
        return False

def update_discord_presence(
    cpu: Dict[str, Any],
    mem: Dict[str, float],
    disk: Optional[Dict[str, float]] = None,
    net: Optional[Dict[str, float]] = None,
    show_os: bool = False
) -> None:
    """Update Discord presence with cross-platform data"""
    global RPC
    if RPC is None or not PYPRESENCE_AVAILABLE:
        return
    
    try:
        variants = get_presence_variants(cpu, mem, disk, net, show_os)
        if not variants:
            return
            
        details, state = random.choice(variants)
        
        # Choose appropriate icons based on OS
        large_image = "system_monitor_logo"
        small_image_map = {
            "Windows": "windows_icon",
            "Darwin": "macos_icon", 
            "Linux": "linux_icon"
        }
        small_image = small_image_map.get(CURRENT_OS, "python_icon")
        
        RPC.update(
            details=details,
            state=state,
            large_image=large_image,
            large_text=f"System Performance Monitor - {OS_NAME}",
            small_image=small_image,
            small_text=f"Monitoring {OS_NAME} System...",
            start=int(initial_script_start_time)
        )
    except Exception as e:
        print(f"Error updating Discord presence: {e}")
        RPC = None

def close_rpc() -> None:
    """Close Discord RPC connection"""
    global RPC
    if RPC and PYPRESENCE_AVAILABLE:
        try:
            RPC.close()
            print("Discord RPC connection closed")
        except Exception as e:
            print(f"Error closing Discord RPC: {e}")
    RPC = None

def check_dependencies():
    """Check if required dependencies are available"""
    missing_deps = []
    
    try:
        import psutil
    except ImportError:
        missing_deps.append("psutil")
    
    if not PYPRESENCE_AVAILABLE:
        missing_deps.append("pypresence")
    
    if missing_deps:
        print(f"Error: Missing required dependencies: {', '.join(missing_deps)}")
        if CURRENT_OS == "Windows":
            print("Install with: pip install " + " ".join(missing_deps))
        else:
            print("Install with: pip install " + " ".join(missing_deps))
            print("Or use a virtual environment:")
            print("python -m venv venv")
            if CURRENT_OS == "Windows":
                print("venv\\Scripts\\activate")
            else:
                print("source venv/bin/activate")
            print("pip install " + " ".join(missing_deps))
        return False
    
    return True

def main():
    global last_rpc_update_time, initial_script_start_time

    print(f"System Monitor starting on {OS_NAME} ({platform.platform()})")
    
    if not check_dependencies():
        sys.exit(1)

    args = parse_args()
    rpc_update_interval = args.rpc_update_interval
    discord_client_id = args.discord_client_id
    show_os = args.show_os

    if not (PYPRESENCE_AVAILABLE and discord_client_id != "YOUR_CLIENT_ID_HERE"):
        print("Discord RPC not available or client ID not set.")
        print("Running in monitor-only mode...")
        # Could add console output mode here if desired
        return

    initial_script_start_time = time.time()
    last_rpc_update_time = 0

    # Get system info for logging
    sys_info = get_system_info()
    print(f"Monitoring system: {sys_info.get('processor', 'Unknown')} on {sys_info['os']}")

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
                        net_data,
                        show_os
                    )
                    last_rpc_update_time = current_time

            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nShutting down system monitor...")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        if PYPRESENCE_AVAILABLE:
            close_rpc()

if __name__ == "__main__":
    main()