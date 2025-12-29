"""
{
    "finishedAt": "1638879833",
    "checkResults": [
        {
"name": "UsedDiskSpace",
"label": "Used Disk Space",
"status": "failed",
"notificationMessage": "The disk is almost full (91% used)",
"shortSummary": "91%",
"meta": {
    "disk_space_used_percentage": 91
}
        },
        {
            "name": "Redis",
            "label": "redis",
            "status": "ok",
            "notificationMessage": "",
            "shortSummary": "Available",
            "meta": []
        }
    ]
}
#The JSON should have two toplevel properties:
finishedAt: a unix timestamp indicating when these check did run on your server.
checkResults: an array with check results. This array can have 50 items maximum.

#A check result should have these properties, they are all required:
name: this should be a unique value to identify this check. We'll use this value to synchronise the check results in our database.
label: a string describing your health check that we will display at the application health checks list.
status: a string that indicates what the result of the health check is. Check below for possible values.
notificationMessage: when a check results in warning or error, we'll use this string in the notification that we'll send to you. we'll also display it at the application health checks list.
shortSummary: a very short summary of the result of your check that will be displayed at the application health checks list.
meta: an array with keys and values that contain extra information about the check. You can send a maximum of 20 items in this array.

#These are the possible values for status:
ok: the check ran ok
warning: the check is closed to failing
failed: the check did fail
crashed: something went wrong running the check itself
skipped: the check wasn't performed at all
"""

import json
from pymongo import MongoClient
from datetime import datetime
import socketio
# import asyncio
import shutil
import math
import psutil
import subprocess
import signal
import time
from pathlib import Path
import os
from typing import List, Optional, Union, Tuple
import json

from flask import current_app as app



from ext.scf import SIO_URL

STATUSES = ['ok', 'warning', 'failed', 'crashed', 'skipped']

SIO_CHECKS = {'endpoints': []}
SIO_MSG = None
SIO_READY = False


class SocketIOHealthChecker:
    """
    Encapsulated Socket.IO client for health checking.
    Safe to use even when connection fails.
    """
    def __init__(self, url: str, timeout: float = 10.0):
        self.url = url
        self.timeout = timeout
        self.sio = socketio.Client()

        self._connected = False
        self._last_result: Optional[Tuple[bool, List[str], List[str]]] = None

        # Register events only once
        self._register_events()

    def _register_events(self):
        @self.sio.event
        def connect():
            self._connected = True
            try:
                app.logger.debug("[SIO Health] Connected")
            except:
                print("[SIO Health] Connected")

        @self.sio.event
        def disconnect():
            self._connected = False
            try:
                app.logger.debug("[SIO Health] Disconnected")
            except:
                print("[SIO Health] Disconnected")

        @self.sio.event
        def connect_error(data):
            self._connected = False
            try:
                app.logger.debug(f"[SIO Health] Connection failed: {data}")
            except:
                print(f"[SIO Health] Connection failed: {data}")

        @self.sio.event
        def health_check_response(data):
            socket_services = {'melwin', 'mailchimp', 'sendgrid'}

            connected_clients = set(data.get('clients', []))

            all_essential = socket_services.issubset(connected_clients)
            running = list(connected_clients & socket_services | {'notification'})
            missing = list(socket_services - connected_clients)

            self._last_result = (all_essential, running, missing)

            try:
                app.logger.debug(f"[SIO Health] Server reported clients: {connected_clients}")
            except:
                print(f"[SIO Health] Server reported clients: {connected_clients}")

            if not all_essential:
                try:
                    app.logger.error(f"[SIO Health] Missing: {missing}")
                except:
                    print(f"[SIO Health] Missing: {missing}")




    def connect(self) -> bool:
        """Try to connect. Returns True if successful."""
        if self._connected:
            return True

        try:
            self.sio.connect(
                self.url,
                # transports=['websocket', 'polling'],
                # wait_timeout=3.0
            )
            # Give a little time for the connect event
            time.sleep(0.4)
            return self._connected
        except Exception as e:
            try:
                app.logger.exception(f"[SIO Health] Connection failed: {e}")
            except:
                print(f"[SIO Health] Connection failed: {e}")
            return False

    def is_connected(self) -> bool:
        return self._connected

    def perform_check(self) -> Tuple[bool, List[str], List[str]]:
        """
        Returns:
            (success: bool, running_services: list, missing_services: list)
        """
        if not self.connect():
            try:
                app.logger.debug("If we can't even connect → everything is missing")
            except:
                print("If we can't even connect → everything is missing")
            return False, [], ['melwin', 'mailchimp', 'sendgrid']

        self._last_result = None  # reset

        try:
            self.sio.emit('handle_health_check', {})

            waited = 0
            step = 0.4
            while waited < self.timeout:
                if self._last_result is not None:
                    return self._last_result
                time.sleep(step)
                waited += step

            try:
                app.logger.error("[SIO Health] Health check timed out")
            except:
                print("[SIO Health] Health check timed out")
            return False, [], ['melwin', 'mailchimp', 'sendgrid']

        except Exception as e:
            try:
                app.logger.exception(f"[SIO Health] Error during check: {e}")
            except:
                print(f"[SIO Health] Error during check: {e}")
            return False, [], ['melwin', 'mailchimp', 'sendgrid']

    def close(self):
        """Clean shutdown"""
        if self._connected:
            try:
                self.sio.disconnect()
            except:
                pass
        self._connected = False


def get_socket_ohdear_response(checker: SocketIOHealthChecker) -> dict:
    ok, running, missing = checker.perform_check()

    essential = {"melwin", "mailchimp", "sendgrid"}
    all_connected = essential.issubset(running)

    if all_connected:
        return {
            "name": "Socket.io daemon checks",
            "label": "socket.io",
            "status": "ok",
            "message": "All essential Socket.IO services connected",
            "short_message": "Socket.IO healthy",
            "meta": {
                "connected": sorted(running),
                "missing": []
            }
        }
    else:
        return {
            "name": "Socket.io daemon checks",
            "label": "socket.io",
            "status": "fail",
            "message": f"Missing essential services: {', '.join(missing)}",
            "short_message": "Socket.IO degraded",
            "meta": {
                "connected": sorted(running),
                "missing": sorted(missing)
            }
        }


def get_socket_ohdear_multi_response(checker: SocketIOHealthChecker) -> list[dict]:
    _, running, missing = checker.perform_check()
    essential = {"melwin", "mailchimp", "sendgrid"}

    result = []
    for service in essential:
        if service in running:
            result.append({
                "name": f"Socket.IO – {service.title()}",
                "label": service.title(),
                "status": "ok",
                "message": f"{service} connected"
            })
        else:
            result.append({
                "name": f"Socket.IO – {service.title()}",
                "label": service.title(),
                "status": "fail",
                "message": f"{service} not connected"
            })

    return result

def _bytes_to_gb(bytes_value):
    return bytes_value / (1024 ** 3)


def check_mongo():
    try:
        client = MongoClient("mongodb://localhost:27017/")
        info = client.server_info()
        return {
            "name": "MongoDB connection test",
            "label": "mongo",
            "status": "ok",
            "notificationMessage": "",
            "shortSummary": "Available",
            "meta": [info]
        }
    except Exception as e:
        return {
            "name": "MongoDB",
            "label": "mongo",
            "status": "failed",
            "notificationMessage": "",
            "shortSummary": "",
            "meta": [e]
        }


def check_disk(path='/'):
    try:
        usage = shutil.disk_usage(path)
        usage_pct = usage.used / usage.total
        status = 'ok'
        if usage_pct > 0.9:
            status = 'warning'
        elif usage_pct > 0.99:
            status = 'failed'

        return {
            "name": "Disk Usage",
            "label": "disk",
            "status": status,
            "notificationMessage": f"Disk usage at {round(usage_pct * 100, 2)}%",
            "shortSummary": "Just fine" if usage_pct < 0.9 else ("Disk is almost full" if usage_pct < 0.99 else "Critical disk usage!"),
            "meta": [
                {
                    'total': f"{round(_bytes_to_gb(usage.total), 2)}G",
                    'used': f"{round(_bytes_to_gb(usage.used), 2)}G",
                    'free': f"{round(_bytes_to_gb(usage.free), 2)}G",
                },
                {'disk_usage': round(usage.used / usage.total, 2)},
                {'disk_free': round(usage.free / usage.total, 2)}]
        }

    except Exception as e:
        return {
            "name": "Disk Ussage",
            "label": "disk",
            "status": "crashed",
            "notificationMessage": "",
            "shortSummary": "",
            "meta": [e]
        }


"""
Obsreg
def check_flightlog():
    pass
def check_eccairs2():
    pass
"""


def check_sendgrid():
    pass


def check_mailchimp():
    pass


def check_fai():
    pass


def check_flydrone():
    pass


def check_tms():
    pass


def _nif_web():
    pass


def _nif_soap_services():
    pass


def _nif_rest_apis():
    pass


def check_nif():
    pass

def find_process_by_filename(filename):
    found_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Check if the process command line contains the filename
            if proc.info['cmdline'] and any(filename in arg for arg in proc.info['cmdline']):
                found_processes.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return found_processes


def format_bytes(bytes_val: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024:
            return f"{bytes_val:.1f}{unit}" if unit != 'B' else f"{bytes_val}{unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f}PB"


def format_uptime(seconds: float) -> str:
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    parts = []
    if days:   parts.append(f"{days}d")
    if hours:  parts.append(f"{hours}h")
    if minutes or not parts: parts.append(f"{minutes}m")
    return " ".join(parts) if parts else "0m"


def server_health_ohdear(
        name: str = "ServerHealth",
        label: str = "Server Resources",
        critical_disk_paths: list = None,  # e.g. ["/", "/var", "/home"]
        warning_percent: int = 80,
        critical_percent: int = 90
) -> dict:
    """
    Generic server-wide health check.
    """
    if critical_disk_paths is None:
        critical_disk_paths = ["/"]

    # CPU
    cpu_percent = psutil.cpu_percent(interval=1)

    # Memory
    mem = psutil.virtual_memory()
    mem_total_gb = mem.total / (1024 ** 3)
    mem_used_gb = mem.used / (1024 ** 3)
    mem_percent = mem.percent

    # Swap
    swap = psutil.swap_memory()
    swap_percent = swap.percent

    # Load average
    load1, load5, load15 = os.getloadavg()

    # System uptime
    boot_time = psutil.boot_time()
    uptime_sec = time.time() - boot_time
    uptime_str = format_uptime(uptime_sec)

    # Disk usage
    disk_checks = []
    highest_disk_percent = 0
    for path in critical_disk_paths:
        try:
            usage = shutil.disk_usage(path)
            percent = usage.used / usage.total * 100
            highest_disk_percent = max(highest_disk_percent, percent)
            disk_checks.append({
                "mount": path,
                "total": format_bytes(usage.total),
                "used": format_bytes(usage.used),
                "free": format_bytes(usage.free),
                "percent": round(percent, 1)
            })
        except Exception as e:
            disk_checks.append({"mount": path, "error": str(e)})

    # Temperature (optional, Linux only)
    temps = {}
    try:
        t = psutil.sensors_temperatures()
        if 'coretemp' in t:
            for entry in t['coretemp']:
                if entry.current:
                    temps[entry.label or entry.name] = entry.current
        elif t:
            for temps_name, entries in t.items():
                for e in entries:
                    if e.current:
                        temps[temps_name] = e.current
    except Exception:
        pass

    # Logged in users
    users = len(psutil.users())

    # Meta with everything
    meta = {
        "cpu_percent": round(cpu_percent, 1),
        "cpu_cores": psutil.cpu_count(),
        "memory_total_gb": round(mem_total_gb, 1),
        "memory_used_gb": round(mem_used_gb, 1),
        "memory_percent": round(mem_percent, 1),
        "swap_percent": round(swap_percent, 1),
        "load_average": [round(load1, 2), round(load5, 2), round(load15, 2)],
        "uptime": uptime_str,
        "uptime_seconds": int(uptime_sec),
        "boot_time_iso": datetime.fromtimestamp(boot_time).isoformat(),
        "logged_in_users": users,
        "disk_usage": disk_checks,
        "highest_disk_percent": round(highest_disk_percent, 1),
        "temperature_celsius": temps or None,
    }

    # Decide status
    if (cpu_percent > 95 or
            mem_percent > 95 or
            swap_percent > 80 or
            highest_disk_percent > critical_percent):
        status = "failed"
        summary = "CRITICAL"
    elif (cpu_percent > 80 or
          mem_percent > warning_percent or
          highest_disk_percent > warning_percent):
        status = "warning"
        summary = "Warning"
    else:
        status = "ok"
        summary = "Healthy"

    # Human notification
    disk_str = f"disk {highest_disk_percent:.0f}%" if highest_disk_percent > 10 else "disk OK"
    notification = f"CPU {cpu_percent:.0f}% • RAM {mem_percent:.0f}% ({mem_used_gb:.1f}GB) • {disk_str} • ↑{uptime_str.split()[0]}"

    return {
        "name": name,
        "label": label,
        "status": status,
        "notificationMessage": notification,
        "shortSummary": summary,
        "meta": meta
    }


def check_service_health(
        pid_file: Optional[Union[str, Path]] = None,
        *,
        exe_path: Optional[Union[str, Path]] = None,
        cwd: Optional[Union[str, Path]] = None,
        cmdline_contains: Optional[Union[str, List[str]]] = None,
        cmdline_exact: Optional[List[str]] = None,
        allow_multiple: bool = False,  # default: expect exactly ONE process
        expect_multiple: bool = None,  # deprecated — use allow_multiple=True instead
) -> dict:
    """
    - allow_multiple=False (default) → expects exactly 1 process → healthy only if 1 found
    - allow_multiple=True             → accepts 1 or more → healthy as long as ≥1 alive
    """
    candidates = []

    # 1. PID file handling (takes priority)
    if pid_file:
        pid_file = Path(pid_file)
        if not pid_file.exists():
            return {"healthy": False, "status": "pid_file_missing", "reason": f"PID file missing: {pid_file}"}
        try:
            pid = int(pid_file.read_text().strip())
            candidates = [psutil.Process(pid)]
        except Exception as e:
            return {"healthy": False, "status": "pid_file_error", "reason": f"Cannot read PID file: {e}"}

    # 2. Search by criteria
    if not candidates:
        substrs = None
        if cmdline_contains:
            substrs = [cmdline_contains] if isinstance(cmdline_contains, str) else cmdline_contains

        for p in psutil.process_iter(['pid', 'exe', 'cwd', 'cmdline']):
            if p.pid <= 1:  # skip init/systemd/kernel
                continue
            try:
                matches = True

                if exe_path and p.exe() and Path(p.exe()) != Path(exe_path).resolve():
                    matches = False
                if cwd and p.cwd() and Path(p.cwd()) != Path(cwd).resolve():
                    matches = False
                if cmdline_exact and p.cmdline() != cmdline_exact:
                    matches = False
                if substrs:
                    cmd = " ".join(p.cmdline() or [])
                    if not any(s in cmd for s in substrs):
                        matches = False

                if matches:
                    candidates.append(p)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

    if not candidates:
        return {
            "healthy": False,
            "status": "not_running",
            "reason": "No matching process found",
            "process_count": 0,
            "pids": []
        }

    # Health filtering (remove zombies, dead, etc.)
    healthy_procs = []
    for p in candidates:
        try:
            if p.status() == psutil.STATUS_ZOMBIE:
                continue
            os.kill(p.pid, 0)  # quick aliveness check
            healthy_procs.append(p)
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            # AccessDenied from root-owned process → assume alive
            healthy_procs.append(p)
        except OSError:
            pass  # probably dead

    process_count = len(healthy_procs)
    if process_count == 0:
        return {
            "healthy": False,
            "status": "all_dead_or_zombie",
            "reason": "All candidate processes are dead or zombies",
            "process_count": 0,
            "pids": []
        }

    # Decision logic (this is the important fix!)
    if not allow_multiple:
        # Strict mode: exactly ONE process expected
        if process_count == 1:
            proc = healthy_procs[0]
            return {
                "healthy": True,
                "status": "running",
                "reason": "Service running (1 healthy process)",
                "process_count": 1,
                "pid": proc.pid,
                "pids": [proc.pid],
                "process": proc,
                "cmdline": proc.cmdline(),
                "cwd": proc.cwd(),
            }
        else:
            # More than one → unhealthy (unless allow_multiple=True)
            return {
                "healthy": False,
                "status": "unexpected_multiple",
                "reason": f"Expected 1 process but found {process_count}",
                "process_count": process_count,
                "pids": [p.pid for p in healthy_procs],
            }
    else:
        # allow_multiple=True → healthy as long as ≥1 process is alive
        oldest = min(healthy_procs, key=lambda p: p.create_time())
        return {
            "healthy": True,
            "status": "running",
            "reason": f"Service running ({process_count} healthy process(es))",
            "process_count": process_count,
            "pid": oldest.pid,  # "main" process = oldest
            "pids": [p.pid for p in healthy_procs],
            "process": oldest,
            "cmdline": oldest.cmdline(),
            "cwd": oldest.cwd(),
        }


def format_uptime(seconds: float) -> str:
    """Convert seconds → human readable string like '3d 12h 45m'"""
    if seconds < 0:
        return "0s"
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    parts = []
    if days:    parts.append(f"{days}d")
    if hours:   parts.append(f"{hours}h")
    if minutes: parts.append(f"{minutes}m")
    if secs or not parts: parts.append(f"{secs}s")
    return " ".join(parts)


def check_service_health_ohdear(
        name: str = "ProcessCheck",
        label: str = "Process Health",
        *,
        pid_file: Optional[Union[str, Path]] = None,
        exe_path: Optional[Union[str, Path]] = None,
        cwd: Optional[Union[str, Path]] = None,
        cmdline_contains: Optional[Union[str, List[str]]] = None,
        cmdline_exact: Optional[List[str]] = None,
        allow_multiple: bool = False,
        cpu_measurement_interval: float = 0.5,  # seconds — small delay for accurate CPU %
) -> dict:
    """
    Full Oh Dear custom check with:
    - Process count
    - Memory (RSS + %)
    - CPU % (accurate, measured over interval)
    - Uptime (human + seconds)
    - Start time
    """
    candidates = []

    # 1. PID file priority
    if pid_file:
        pid_file = Path(pid_file)
        if not pid_file.exists():
            return {
                "name": name, "label": label, "status": "failed",
                "notificationMessage": f"PID file missing: {pid_file}",
                "shortSummary": "No PID file",
                "meta": {"pid_file": str(pid_file)}
            }
        try:
            pid = int(pid_file.read_text().strip())
            candidates = [psutil.Process(pid)]
        except Exception as e:
            return {
                "name": name, "label": label, "status": "failed",
                "notificationMessage": f"Invalid PID file: {e}",
                "shortSummary": "Bad PID",
                "meta": {"error": str(e)}
            }

    # 2. Search processes
    if not candidates:
        substrs = [cmdline_contains] if isinstance(cmdline_contains, str) else cmdline_contains or []

        for p in psutil.process_iter(['pid', 'exe', 'cwd', 'cmdline', 'create_time']):
            if p.pid <= 1:
                continue
            try:
                matches = True
                if exe_path and p.exe() and Path(p.exe()).resolve() != Path(exe_path).resolve():
                    matches = False
                if cwd and p.cwd() and Path(p.cwd()).resolve() != Path(cwd).resolve():
                    matches = False
                if cmdline_exact and p.cmdline() != cmdline_exact:
                    matches = False
                if substrs:
                    cmd = " ".join(p.cmdline() or [])
                    if not any(s in cmd for s in substrs):
                        matches = False
                if matches:
                    candidates.append(p)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

    # Filter healthy (alive) processes
    healthy_procs = []
    for p in candidates:
        try:
            if p.status() == psutil.STATUS_ZOMBIE:
                continue
            os.kill(p.pid, 0)
            healthy_procs.append(p)
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            healthy_procs.append(p)
        except OSError as e:
            print(e)

    count = len(healthy_procs)
    pids = [p.pid for p in healthy_procs]

    total_ram_mb = psutil.virtual_memory().total / 1024 / 1024

    meta = {
        "process_count": count,
        "pids": pids,
        "allow_multiple": allow_multiple,
        "expected": "multiple" if allow_multiple else "single",
    }

    if count == 0:
        return {
            "name": name, "label": label, "status": "failed",
            "notificationMessage": "No running process found",
            "shortSummary": "Down",
            "meta": meta
        }

    # Accurate CPU measurement (requires two samples)
    try:
        # First sample
        cpu_times_before = {p.pid: p.cpu_times() for p in healthy_procs}
        time.sleep(cpu_measurement_interval)
        # Second sample
        cpu_percents = []
        for p in healthy_procs:
            try:
                # This gives accurate CPU % over the interval
                cpu_percent = p.cpu_percent(interval=None)  # None = use cached value from previous call
                cpu_percents.append(cpu_percent)
            except Exception as e:
                print(e)
                cpu_percents.append(0.0)

        total_cpu_percent = sum(cpu_percents)
        avg_cpu_percent = total_cpu_percent / len(cpu_percents) if cpu_percents else 0.0
    except Exception as e:
        total_cpu_percent = avg_cpu_percent = 0.0
        meta["cpu_measurement_error"] = str(e)

    # Main process (oldest = parent)
    main_proc = min(healthy_procs, key=lambda p: p.create_time())
    try:
        mem = main_proc.memory_info()
        mem_rss_mb = mem.rss / 1024 / 1024
        mem_percent = main_proc.memory_percent()
        started_ts = main_proc.create_time()
        uptime_sec = time.time() - started_ts
        uptime_str = format_uptime(uptime_sec)

        meta.update({
            "main_pid": main_proc.pid,
            "cmdline": main_proc.cmdline(),
            "exe": main_proc.exe(),
            "cwd": main_proc.cwd(),
            "started_at_unix": started_ts,
            "started_at_iso": datetime.fromtimestamp(started_ts).isoformat(),
            "uptime": uptime_str,
            "uptime_seconds": int(uptime_sec),
            "memory_rss_mb": round(mem_rss_mb, 1),
            "memory_percent": round(mem_percent, 2),
            "total_ram_mb": round(total_ram_mb, 1),
            "cpu_percent_total": round(total_cpu_percent, 2),
            "cpu_percent_average": round(avg_cpu_percent, 2),
            "cpu_measurement_interval": cpu_measurement_interval,
        })
    except Exception as e:
        meta["detail_error"] = str(e)

    # Decision
    if not allow_multiple and count > 1:
        return {
            "name": name, "label": label, "status": "failed",
            "notificationMessage": f"Expected 1 process but found {count}",
            "shortSummary": f"{count} instances",
            "meta": meta
        }

    # All good
    ram_str = f"{int(mem_rss_mb)} MB"
    cpu_str = f"{total_cpu_percent:.1f}% CPU" if total_cpu_percent > 0 else "0% CPU"

    return {
        "name": name,
        "label": label,
        "status": "ok",
        "notificationMessage": f"{count} process(es) • Uptime {uptime_str} • {ram_str} • {cpu_str}",
        "shortSummary": f"{count} ↑{uptime_str.split()[0]} {ram_str}",
        "meta": meta
    }

def check_systemd_service_ohdear(
    service_name: str,                  # e.g. "mongod" or "mongod.service"
    name: Union[str, None] = None,  # ← Fixed: old Union syntax
    label: Union[str, None] = None,  # ← Fixed
) -> dict:
    """
    Checks a systemd service and returns Oh Dear formatted JSON.
    Uses systemctl show for accurate status, memory, CPU usage, start time.
    """
    if not name:
        name = service_name.replace(".service", "").capitalize()
    if not label:
        label = f"{name} Service"

    # Strip .service if provided
    if service_name.endswith(".service"):
        service_name = service_name[:-8]

    # Get key properties from systemd
    try:
        result = subprocess.check_output(
            ["systemctl", "show", "-p", "ActiveState,SubState,MainPID,ExecMainStartTimestamp,MemoryCurrent,CPUUsageNSec,ExecMainStatus", f"{service_name}.service"],
            universal_newlines=True
        )
    except subprocess.CalledProcessError as e:
        return {
            "name": name,
            "label": label,
            "status": "failed",
            "notificationMessage": f"Failed to query systemd: exit code {e.returncode}",
            "shortSummary": "Query failed",
            "meta": {"service": service_name, "error": "systemctl command failed"}
        }
    except FileNotFoundError:
        return {
            "name": name,
            "label": label,
            "status": "failed",
            "notificationMessage": "systemctl not found (not a systemd system?)",
            "shortSummary": "No systemd",
            "meta": {"service": service_name}
        }

    props = {}
    for line in result.strip().splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            props[k] = v

    active_state = props.get("ActiveState", "unknown")
    sub_state = props.get("SubState", "unknown")
    main_pid = props.get("MainPID", "0")
    start_timestamp = props.get("ExecMainStartTimestamp", "")
    memory_current = props.get("MemoryCurrent", "0")
    cpu_nsec = props.get("CPUUsageNSec", "0")
    exit_status = props.get("ExecMainStatus", "0")

    meta = {
        "service": f"{service_name}.service",
        "active_state": active_state,
        "sub_state": sub_state,
        "main_pid": int(main_pid) if main_pid.isdigit() else None,
        "exit_status": int(exit_status),
    }

    # Parse start time and calculate uptime
    uptime_str = "unknown"
    uptime_seconds = 0
    if start_timestamp and start_timestamp != "-":
        # Example: "Thu 2025-12-18 14:22:10 UTC"
        try:
            dt = datetime.strptime(start_timestamp, "%a %Y-%m-%d %H:%M:%S %Z")
            uptime_seconds = int(time.time() - dt.timestamp())
            uptime_str = format_uptime(uptime_seconds)
            meta["started_at_iso"] = dt.isoformat()
            meta["uptime"] = uptime_str
            meta["uptime_seconds"] = uptime_seconds
        except ValueError:
            pass  # fallback to unknown

    # Memory (MemoryCurrent is in bytes, [unknown] if not available)
    if memory_current.isdigit():
        mem_mb = int(memory_current) / 1024 / 1024
        meta["memory_mb"] = round(mem_mb, 1)
        ram_str = f"{round(mem_mb)} MB"
    else:
        ram_str = "N/A"
        meta["memory_mb"] = None

    # CPU usage (total nanoseconds → approximate % over uptime)
    if cpu_nsec.isdigit() and uptime_seconds > 0:
        cpu_sec_total = int(cpu_nsec) / 1e9
        cpu_percent = (cpu_sec_total / uptime_seconds) * 100
        meta["cpu_percent_lifetime"] = round(cpu_percent, 2)
        cpu_str = f"{cpu_percent:.1f}%"
    else:
        cpu_str = "N/A"
        meta["cpu_percent_lifetime"] = None

    # Decide status
    if active_state == "active" and sub_state in {"running", "exited"}:  # exited is OK for oneshot
        status = "ok"
        notification = f"{service_name} is active • Uptime {uptime_str} • RAM {ram_str} • CPU {cpu_str}"
        short_summary = "Running"
    elif active_state == "failed":
        status = "failed"
        notification = f"{service_name} has failed (exit code {exit_status})"
        short_summary = "Failed"
    elif active_state == "inactive":
        status = "failed"
        notification = f"{service_name} is inactive"
        short_summary = "Stopped"
    else:
        status = "warning"
        notification = f"{service_name} in {active_state}/{sub_state} state"
        short_summary = "Degraded"

    return {
        "name": name,
        "label": label,
        "status": status,
        "notificationMessage": notification,
        "shortSummary": short_summary,
        "meta": meta
    }

if __name__ == '__main__':

    print(check_disk())
    """
    # 3.7-> asyncio.run(check_server_status('http://localhost:7000'))
    print(perform_socketio_check(SIO_URL))

    # check_server_status(SIO_URL)
    # print(find_process_by_filename('notification_daemon.py'))
    # print(find_process_by_filename('melwin_daemon.py'))
    # print(find_process_by_filename('sendgrid_daemon.py'))
    # print(find_process_by_filename('nlf-auth'))
    # print(find_process_by_filename('melwin.py'))

    # print(check_service_health_ohdear(name='MongoDB (systemd-service)', label='mongo', cmdline_contains=['/usr/bin/mongod'], allow_multiple=True))
    # print(check_service_health_ohdear(name='MongoDB (systemd-service)', label='mongo', pid_file='/storage/mongodb/mongod.lock', allow_multiple=True))
    check_systemd_service_ohdear(service_name='mongod')
    print(check_mongo())

    print(check_service_health(pid_file = "/var/run/nginx.pid",cmdline_contains=["nginx: master process", "nginx"]))
    print(check_service_health_ohdear(name='Notification Daemon (socket.io)', label='notifications', cmdline_contains=['/www/lungo/bin/gunicorn', 'notification_daemon:app'], cwd='/www/lungo', allow_multiple=True))
    print(check_service_health_ohdear(name='Integration Syncronization', label='integration', pid_file='/home/einar/nif-integration/syncdaemon.pid'))
    print(check_service_health_ohdear(name='Integration Stream', label='integration', pid_file='/home/einar/nif-integration/streamdaemon.pid'))
    print(check_service_health_ohdear(name='Membership API', label='lungo', pid_file='/www/lungo/gunicorn.pid'))
    print(check_service_health_ohdear(name='NLF AUTH', label='auth', pid_file='/home/einar/nlf-auth/gunicorn.pid'))
    print(check_service_health_ohdear(name='Spyne for Elefun', label='elefun', cwd="/home/einar/spyne", cmdline_contains=['melwin.py'], allow_multiple=True))
    print(check_service_health_ohdear(name='Membership API', label='lungo', cwd="/www/lungo", cmdline_contains=['/www/lungo/bin/gunicorn', 'run:app'], allow_multiple=True))
    print(server_health_ohdear(critical_disk_paths=["/", "/var", "/home"],warning_percent=75,critical_percent=90))
    """