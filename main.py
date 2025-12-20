import subprocess
import select
import json
import re
import os
import time
import sys
import pwd
import logging
import shutil

# Constants
TARGET_USER_UID = 1000
LOG_FILE = "/var/log/ntfs-auto-fix.log"

# Setup Logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_target_user():
    """Get the username for UID 1000."""
    try:
        return pwd.getpwuid(TARGET_USER_UID).pw_name
    except KeyError:
        return "prabhanshu"

def notify(summary, body, icon="drive-harddisk", replace_id=None, urgency="normal"):
    """
    Send a notification. 
    Returns the notification ID (int) if successful, or None.
    """
    user = get_target_user()
    bus_path = f"/run/user/{TARGET_USER_UID}/bus"
    bus_address = f"unix:path={bus_path}"
    xdg_runtime = f"/run/user/{TARGET_USER_UID}"
    xauthority = f"/home/{user}/.Xauthority"
    
    if not os.path.exists(bus_path):
        logging.error(f"User bus not found at {bus_path}")
        return None

    displays = [":1", ":0"]
    
    for display in displays:
        # We must pass env vars INSIDE the sudo command because sudo scrubs env.
        # Structure: sudo -u user env VAR=VAL command args...
        cmd = [
            "sudo", "-u", user, 
            "env",
            f"DBUS_SESSION_BUS_ADDRESS={bus_address}",
            f"XDG_RUNTIME_DIR={xdg_runtime}",
            f"DISPLAY={display}",
            f"XAUTHORITY={xauthority}",
            "notify-send", 
            "-i", icon, 
            "-a", "NTFS Auto Fix",
            "-u", urgency,
            "-p" # Print ID
        ]
        
        if replace_id:
            cmd.extend(["-r", str(replace_id)])
            
        cmd.extend([summary, body])
        
        try:
            # Note: We do NOT pass env=... to subprocess.run here, as we are doing it via 'env' command.
            res = subprocess.run(cmd, capture_output=True, text=True)
            
            if res.returncode == 0:
                # Output should be the ID
                try:
                    notif_id = int(res.stdout.strip())
                    logging.info(f"Notification sent (ID: {notif_id}) to {display}: {summary}")
                    return notif_id
                except ValueError:
                    logging.warning(f"Notification sent but ID unreadable: {res.stdout}")
                    return None
            else:
                logging.warning(f"Notification failed on {display} (code {res.returncode}): {res.stderr.strip()}")
        except Exception as e:
            logging.error(f"Notification execution error on {display}: {e}")
            
    return None

def check_dependencies():
    """Check for ntfsfix and notify if missing."""
    if shutil.which("ntfsfix") is None:
        logging.error("ntfsfix command not found.")
        notify(
            "Missing Dependency: ntfsfix", 
            "The <b>ntfsfix</b> tool is required but not found.\n\nPlease install it via terminal:\n<tt>sudo pacman -S ntfs-3g</tt>", 
            "dialog-error",
            urgency="critical"
        )
        return False
    return True

def fix_device(device):
    """Run ntfsfix on the device with a 3-step notification flow."""
    if not device.startswith("/dev/"):
        device = "/dev/" + device
        
    logging.info(f"Starting fix flow for: {device}")
    
    # Step 1: Detection
    notif_id = notify(
        f"NTFS Fix (1/3): Detected",
        f"Unclean file system detected on <b>{device}</b>.\nPreparing to fix...",
        "drive-harddisk-error",
        urgency="critical"
    )
    
    time.sleep(1) # UX pause
    
    # Step 2: Attempting Fix
    notify(
        f"NTFS Fix (2/3): Repairing",
        f"Running <i>ntfsfix</i> on <b>{device}</b>...\nPlease wait.",
        "tools-check-spelling",
        replace_id=notif_id
    )
    
    # Run command
    cmd = ["ntfsfix", "-d", device]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True)
        
        # Step 3: Result
        if res.returncode == 0:
            logging.info(f"Fix successful for {device}")
            notify(
                f"NTFS Fix (3/3): Success",
                f"<b>{device}</b> is now clean.\nYou can access the drive now.\n\n<small>Log: {res.stdout.splitlines()[-1] if res.stdout else 'Fixed'}</small>",
                "emblem-default",
                replace_id=notif_id
            )
        else:
            logging.error(f"Fix failed for {device}: {res.stderr}")
            notify(
                f"NTFS Fix: Failed",
                f"Could not fix <b>{device}</b>.\nError: {res.stderr}",
                "dialog-error",
                replace_id=notif_id,
                urgency="critical"
            )
            
    except FileNotFoundError:
        # Should be caught by check_dependencies, but safe fallback
        notify("Error", "ntfsfix command missing.", "dialog-error")

def monitor_journal():
    """Monitor system journal for NTFS mount errors."""
    
    logging.info(f"Starting NTFS Auto Fix Monitor... (Target user: {get_target_user()})")
    
    cmd = ["journalctl", "-f", "-o", "json"]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    poll_obj = select.poll()
    poll_obj.register(process.stdout, select.POLLIN)
    
    while True:
        poll_result = poll_obj.poll(500) # 0.5s check
        if poll_result:
            line = process.stdout.readline()
            if not line:
                break
            
            try:
                entry = json.loads(line)
                msg = entry.get("MESSAGE", "")
                
                if "ntfs" in msg.lower() and ("dirty" in msg.lower() or "unclean" in msg.lower() or "refused to mount" in msg.lower()):
                    
                    logging.info(f"Log Hit: {msg}")
                    
                    match = re.search(r"/dev/([a-z]+[0-9]+)", msg)
                    found_dev = None
                    
                    if match:
                        found_dev = match.group(0)
                    else:
                        match = re.search(r"\b([hsv]d[a-z][0-9]+)\b", msg)
                        if match:
                             found_dev = "/dev/" + match.group(1)
                    
                    if found_dev:
                        fix_device(found_dev)
                        time.sleep(3) # Cooldown
                        
            except json.JSONDecodeError:
                pass
            except Exception as e:
                logging.error(f"Error parsing log: {e}")

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("Warning: This script should be run as root to perform fixes.")
    
    # Startup Check
    if check_dependencies():
        notify(
            "NTFS Auto-Fix Service", 
            "<b>Service Started</b>\nMonitoring system logs for mount errors.", 
            "utilities-terminal"
        )
        
    monitor_journal()