import subprocess
import os
import pwd

TARGET_USER_UID = 1000
LOG_FILE = "/var/log/ntfs-auto-fix.log"

def get_target_user():
    try:
        return pwd.getpwuid(TARGET_USER_UID).pw_name
    except KeyError:
        return "prabhanshu"

def test_notify():
    user = get_target_user()
    bus_path = f"/run/user/{TARGET_USER_UID}/bus"
    bus_address = f"unix:path={bus_path}"
    xdg_runtime = f"/run/user/{TARGET_USER_UID}"
    
    print(f"Testing notification for user: {user}")
    
    if not os.path.exists(bus_path):
        print(f"ERROR: User bus socket not found at {bus_path}")
        return

    # Try common displays
    displays = [":1", ":0"] 
    
    for display in displays:
        print(f"\n--- Attempting Display {display} ---")
        
        cmd = [
            "sudo", "-u", user,
            "env",
            f"DBUS_SESSION_BUS_ADDRESS={bus_address}",
            f"XDG_RUNTIME_DIR={xdg_runtime}",
            f"DISPLAY={display}",
            f"XAUTHORITY=/home/{user}/.Xauthority",
            "notify-send",
            "-i", "utilities-terminal",
            "NTFS Fix Test",
            f"Notification test success on {display}!"
        ]
        
        print("Command:", " ".join(cmd))
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"SUCCESS: Notification sent to {display}.")
                return
            else:
                print(f"FAILURE: Return code {result.returncode}")
                print(f"Stderr: {result.stderr.strip()}")
        except Exception as e:
            print(f"EXECUTION ERROR: {e}")
            
    print("\nAll attempts failed.")

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("Please run this script as root to simulate the service environment: sudo python3 test_notify.py")
    else:
        test_notify()
