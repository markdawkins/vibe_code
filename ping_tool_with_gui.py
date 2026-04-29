### Basic Ping tool with a gui  and CSV exports that help track connectvity  with relavant time stamps##############
import csv
import ipaddress
import platform
import queue
import re
import socket
import subprocess
import threading
import time
import tkinter as tk
from datetime import datetime
from tkinter import scrolledtext, ttk

# -----------------------------
# GLOBAL STATE
# -----------------------------
stop_event = threading.Event()
monitoring_running = False
ui_queue = queue.Queue()

# -----------------------------
# TRACKING DICTIONARIES
# -----------------------------
stats = {
    "total_pings": {},
    "success_pings": {},
    "resolved_ip": {},
}

dashboard_labels = {}

# -----------------------------
# LOGGING FUNCTION
# -----------------------------
def log_to_file(text):
    """Append log entries to a daily log file."""
    filename = f"ping_log_{datetime.now().strftime('%Y-%m-%d')}.txt"
    with open(filename, "a", encoding="utf-8") as log:
        log.write(text + "\n")


# -----------------------------
# UI QUEUE HELPERS
# -----------------------------
def post_ui(func, *args, **kwargs):
    """Queue a UI action to run safely on the Tkinter main thread."""
    ui_queue.put((func, args, kwargs))


def process_ui_queue():
    """Process queued UI updates from worker thread."""
    try:
        while True:
            func, args, kwargs = ui_queue.get_nowait()
            func(*args, **kwargs)
    except queue.Empty:
        pass
    root.after(100, process_ui_queue)


# -----------------------------
# UI UPDATE FUNCTIONS
# -----------------------------
def append_output(text, tag=None):
    output_box.insert(tk.END, text, tag)
    output_box.see(tk.END)


def clear_output():
    output_box.delete("1.0", tk.END)


def rebuild_dashboard(targets):
    for widget in dash_frame.winfo_children():
        widget.destroy()

    dashboard_labels.clear()

    for target in targets:
        lbl = tk.Label(
            dash_frame,
            text=f"{target} — 0.00% Uptime",
            font=("Arial", 11)
        )
        lbl.pack(anchor="w", padx=10)
        dashboard_labels[target] = lbl


def update_dashboard_snapshot(snapshot):
    """
    snapshot format:
    {
        "host1": (total, success),
        "host2": (total, success),
    }
    """
    for target, (total, success) in snapshot.items():
        uptime = (success / total * 100) if total > 0 else 0.0
        if target in dashboard_labels:
            dashboard_labels[target].config(
                text=f"{target} — {uptime:.2f}% Uptime"
            )


def set_progress(bar, value=None, maximum=None):
    if maximum is not None:
        bar["maximum"] = maximum
    if value is not None:
        bar["value"] = value


def set_countdown_label(text):
    countdown_var.set(text)


def set_controls_running(is_running):
    global monitoring_running
    monitoring_running = is_running

    state_running = tk.DISABLED if is_running else tk.NORMAL
    stop_state = tk.NORMAL if is_running else tk.DISABLED

    start_button.config(state=state_running)
    stop_button.config(state=stop_state)
    ip_entry.config(state=state_running)
    cycles_spin.config(state=state_running)
    delay_entry.config(state=state_running)


def finish_run(final_message, csv_filename=None, tag="done"):
    """Called on main thread when worker finishes or stops."""
    append_output("\n" + final_message + "\n", tag)
    log_to_file(final_message)

    if csv_filename:
        export_msg = f"📄 CSV exported: {csv_filename}"
        append_output(export_msg + "\n", "header")
        log_to_file(export_msg)

    set_controls_running(False)
    set_countdown_label("Countdown: Idle")


# -----------------------------
# VALIDATION HELPERS
# -----------------------------
HOSTNAME_REGEX = re.compile(
    r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)"
    r"(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))*\.?$"
)


def validate_target(target):
    """
    Validate whether target is a valid IP or resolvable hostname.
    Returns: (is_valid, resolved_ip_or_error)
    """
    target = target.strip()
    if not target:
        return False, "Empty value"

    # Try IP address first
    try:
        ipaddress.ip_address(target)
        return True, target
    except ValueError:
        pass

    # Validate hostname pattern
    if not HOSTNAME_REGEX.match(target):
        return False, "Invalid hostname format"

    # Try DNS resolution
    try:
        resolved = socket.gethostbyname(target)
        return True, resolved
    except socket.gaierror:
        return False, "Hostname could not be resolved"


def validate_inputs():
    """Validate targets, cycles, and delay settings."""
    raw_targets = ip_entry.get().split()

    if not (2 <= len(raw_targets) <= 20):
        append_output(
            "❌ Please enter between 2 and 20 IP addresses or hostnames.\n",
            "error"
        )
        return None, None, None

    # Validate cycles
    try:
        cycles = int(cycles_var.get())
        if cycles < 1 or cycles > 1000:
            raise ValueError
    except ValueError:
        append_output("❌ Cycles must be an integer from 1 to 1000.\n", "error")
        return None, None, None

    # Validate delay
    try:
        delay_minutes = float(delay_var.get())
        if delay_minutes < 0 or delay_minutes > 1440:
            raise ValueError
    except ValueError:
        append_output(
            "❌ Delay must be a number from 0 to 1440 minutes.\n",
            "error"
        )
        return None, None, None

    # Validate targets
    bad_targets = []
    resolved_map = {}
    normalized_targets = []

    for target in raw_targets:
        valid, result = validate_target(target)
        if not valid:
            bad_targets.append(f"{target} ({result})")
        else:
            normalized_targets.append(target)
            resolved_map[target] = result

    if bad_targets:
        append_output("❌ The following entries are invalid:\n", "error")
        for item in bad_targets:
            append_output(f"   - {item}\n", "error")
        return None, None, None

    return normalized_targets, resolved_map, (cycles, delay_minutes)


# -----------------------------
# CSV EXPORT
# -----------------------------
def export_stats_to_csv(targets, started_at, ended_at, status):
    """
    Export ping summary to CSV.
    Returns the filename.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"ping_stats_{timestamp}.csv"

    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            "Target",
            "Resolved IP",
            "Total Pings",
            "Successful Pings",
            "Failed Pings",
            "Uptime Percent",
            "Run Started",
            "Run Ended",
            "Status"
        ])

        for target in targets:
            total = stats["total_pings"].get(target, 0)
            success = stats["success_pings"].get(target, 0)
            failed = total - success
            uptime = (success / total * 100) if total > 0 else 0.0
            resolved_ip = stats["resolved_ip"].get(target, "")

            writer.writerow([
                target,
                resolved_ip,
                total,
                success,
                failed,
                f"{uptime:.2f}",
                started_at.strftime("%Y-%m-%d %H:%M:%S"),
                ended_at.strftime("%Y-%m-%d %H:%M:%S"),
                status
            ])

    return filename


# -----------------------------
# TIME FORMATTING
# -----------------------------
def format_countdown(seconds):
    mins, secs = divmod(seconds, 60)
    hours, mins = divmod(mins, 60)
    if hours > 0:
        return f"Countdown: {hours:02d}:{mins:02d}:{secs:02d}"
    return f"Countdown: {mins:02d}:{secs:02d}"


# -----------------------------
# PING FUNCTION
# -----------------------------
def ping(target):
    """
    Ping a target and return True/False.
    Uses a short timeout to avoid hanging.
    """
    try:
        system = platform.system().lower()

        if system == "windows":
            command = ["ping", "-n", "1", "-w", "2000", target]  # 2 sec timeout
        else:
            # Linux/macOS style
            command = ["ping", "-c", "1", "-W", "2", target]  # 2 sec timeout

        result = subprocess.run(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False
    except Exception:
        return False


# -----------------------------
# MONITOR WORKER
# -----------------------------
def ping_worker(targets, cycles, delay_minutes):
    started_at = datetime.now()
    delay_seconds = int(delay_minutes * 60)

    for cycle in range(1, cycles + 1):
        if stop_event.is_set():
            break

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        header = f"[{timestamp}] --- Ping Cycle {cycle} of {cycles} ---"
        post_ui(append_output, f"\n{header}\n", "header")
        log_to_file(header)

        post_ui(set_progress, cycle_progress, 0, len(targets))

        for index, target in enumerate(targets, start=1):
            if stop_event.is_set():
                break

            result = ping(target)

            stats["total_pings"][target] += 1
            if result:
                stats["success_pings"][target] += 1

            text = (
                f"{target} ✅ Ping Successful"
                if result else
                f"{target} ❌ Ping Failed"
            )
            tag = "green" if result else "red"

            post_ui(append_output, text + "\n", tag)
            log_to_file(text)

            # Snapshot for dashboard
            snapshot = {
                t: (
                    stats["total_pings"].get(t, 0),
                    stats["success_pings"].get(t, 0)
                )
                for t in targets
            }
            post_ui(update_dashboard_snapshot, snapshot)
            post_ui(set_progress, cycle_progress, index, len(targets))

        post_ui(set_progress, overall_progress, cycle, cycles)

        # Wait before next cycle
        if cycle < cycles and not stop_event.is_set():
            wait_msg = f"Waiting {delay_minutes} minute(s) before next cycle..."
            post_ui(append_output, "\n" + wait_msg + "\n", "header")
            log_to_file(wait_msg)

            if delay_seconds > 0:
                for remaining in range(delay_seconds, 0, -1):
                    if stop_event.is_set():
                        break
                    post_ui(set_countdown_label, format_countdown(remaining))
                    time.sleep(1)

            post_ui(set_countdown_label, "Countdown: Idle")

    ended_at = datetime.now()

    if stop_event.is_set():
        status = "Stopped"
        final_message = "⛔ Monitoring stopped by user."
        tag = "error"
    else:
        status = "Completed"
        final_message = "✅ All ping cycles are completed."
        tag = "done"

    csv_filename = export_stats_to_csv(targets, started_at, ended_at, status)
    post_ui(finish_run, final_message, csv_filename, tag)


# -----------------------------
# START BUTTON FUNCTION
# -----------------------------
def run_pings():
    if monitoring_running:
        append_output("⚠ Monitoring is already running.\n", "error")
        return

    validated_targets, resolved_map, settings = validate_inputs()
    if validated_targets is None:
        return

    cycles, delay_minutes = settings

    # Reset stop flag
    stop_event.clear()

    # Reset stats
    stats["total_pings"].clear()
    stats["success_pings"].clear()
    stats["resolved_ip"].clear()

    for target in validated_targets:
        stats["total_pings"][target] = 0
        stats["success_pings"][target] = 0
        stats["resolved_ip"][target] = resolved_map[target]

    # Reset GUI
    clear_output()
    rebuild_dashboard(validated_targets)
    set_progress(cycle_progress, 0, len(validated_targets))
    set_progress(overall_progress, 0, cycles)
    set_countdown_label("Countdown: Idle")
    set_controls_running(True)

    start_msg = (
        f"▶ Starting monitor for {len(validated_targets)} target(s), "
        f"{cycles} cycle(s), {delay_minutes} minute(s) delay.\n"
    )
    append_output(start_msg, "header")
    log_to_file(start_msg.strip())

    worker = threading.Thread(
        target=ping_worker,
        args=(validated_targets, cycles, delay_minutes),
        daemon=True
    )
    worker.start()


# -----------------------------
# STOP BUTTON FUNCTION
# -----------------------------
def stop_program_now():
    if not monitoring_running:
        return

    if not stop_event.is_set():
        stop_event.set()
        msg = "⛔ Stop requested by user. Finishing current operation..."
        append_output("\n" + msg + "\n", "error")
        log_to_file(msg)


# -----------------------------
# BUILD GUI
# -----------------------------
root = tk.Tk()
root.title("IP Ping Monitor Dashboard V12")
root.geometry("840x760")

# ------------------ Top Frame ------------------
top_frame = tk.Frame(root)
top_frame.pack(pady=8, fill="x")

title_label = tk.Label(
    top_frame,
    text="Enter 2–20 IP Addresses / Hostnames (space-separated):",
    font=("Arial", 12)
)
title_label.pack(pady=5)

ip_entry = tk.Entry(top_frame, width=95, font=("Arial", 12))
ip_entry.pack(pady=5)

# ------------------ Settings Frame ------------------
settings_frame = tk.LabelFrame(root, text="Run Settings", font=("Arial", 12))
settings_frame.pack(pady=8, padx=10, fill="x")

settings_inner = tk.Frame(settings_frame)
settings_inner.pack(pady=8)

tk.Label(settings_inner, text="Cycles:", font=("Arial", 11)).grid(row=0, column=0, padx=6, pady=4, sticky="e")
cycles_var = tk.StringVar(value="5")
cycles_spin = tk.Spinbox(
    settings_inner,
    from_=1,
    to=1000,
    width=8,
    textvariable=cycles_var,
    font=("Arial", 11)
)
cycles_spin.grid(row=0, column=1, padx=6, pady=4)

tk.Label(settings_inner, text="Delay Between Cycles (minutes):", font=("Arial", 11)).grid(row=0, column=2, padx=6, pady=4, sticky="e")
delay_var = tk.StringVar(value="10")
delay_entry = tk.Entry(settings_inner, width=10, textvariable=delay_var, font=("Arial", 11))
delay_entry.grid(row=0, column=3, padx=6, pady=4)

countdown_var = tk.StringVar(value="Countdown: Idle")
countdown_label = tk.Label(
    settings_frame,
    textvariable=countdown_var,
    font=("Arial", 11, "bold"),
    fg="darkblue"
)
countdown_label.pack(pady=4)

# ------------------ Button Frame ------------------
button_frame = tk.Frame(root)
button_frame.pack(pady=10)

start_button = tk.Button(
    button_frame,
    text="Start Pinging",
    font=("Arial", 12),
    width=14,
    command=run_pings
)
start_button.grid(row=0, column=0, padx=10)

stop_button = tk.Button(
    button_frame,
    text="STOP",
    font=("Arial", 12),
    width=10,
    bg="red",
    fg="white",
    state=tk.DISABLED,
    command=stop_program_now
)
stop_button.grid(row=0, column=1, padx=10)

# ------------------ Dashboard ------------------
dash_frame = tk.LabelFrame(root, text="Uptime Dashboard", font=("Arial", 12))
dash_frame.pack(pady=10, padx=10, fill="x")

# ------------------ Progress Bars ------------------
progress_frame = tk.LabelFrame(root, text="Progress", font=("Arial", 12))
progress_frame.pack(pady=10, padx=10, fill="x")

tk.Label(progress_frame, text="Cycle Progress", font=("Arial", 11)).pack(pady=(8, 0))
cycle_progress = ttk.Progressbar(progress_frame, length=500)
cycle_progress.pack(pady=5)

tk.Label(progress_frame, text="Overall Progress", font=("Arial", 11)).pack(pady=(8, 0))
overall_progress = ttk.Progressbar(progress_frame, length=500)
overall_progress.pack(pady=5)

# ------------------ Output Box ------------------
output_box = scrolledtext.ScrolledText(
    root,
    width=100,
    height=20,
    font=("Consolas", 11)
)
output_box.pack(pady=10, padx=10)

# Text Color Tags
output_box.tag_config("green", foreground="green")
output_box.tag_config("red", foreground="red")
output_box.tag_config("error", foreground="red", font=("Arial", 12, "bold"))
output_box.tag_config("header", foreground="blue", font=("Arial", 12, "bold"))
output_box.tag_config("done", foreground="purple", font=("Arial", 12, "bold"))

# Start UI queue processor
root.after(100, process_ui_queue)

root.mainloop()
