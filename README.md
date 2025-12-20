# NTFS Auto Fix Service

A lightweight background service for Linux that automatically repairs NTFS drive errors (dirty bit/mount refusal) using `ntfsfix`.

## Problem
On some Linux systems (like Arch/Omarchy), external NTFS drives may refuse to mount due to the "dirty bit" being set (often caused by unsafe removal from Windows). Users typically have to manually run `ntfsfix`.

## Solution
This utility runs as a system service. It monitors the system logs for NTFS mount failures. When a failure is detected:
1. It sends a desktop notification: "Detected error... fixing".
2. It runs `ntfsfix -d` on the affected drive.
3. It sends a success notification: "Ready to access".
4. You can then click the drive again to mount it successfully.

## Features
- **Zero Configuration:** Just install and forget.
- **Resource Efficient:** Does not poll drives. It waits for log events (using `journalctl`).
- **Safe:** Does not auto-mount. It only fixes the filesystem structure when you try (and fail) to access it.
- **Visual Feedback:** Uses native desktop notifications (`notify-send`) to keep you informed.
- **Logging:** Logs activity to `/var/log/ntfs-auto-fix.log`.

## Installation

1.  Clone or download this folder.
2.  Open a terminal in this directory.
3.  Run the installer:
    ```bash
    sudo ./install.sh
    ```

## Uninstallation

Run the uninstaller:
```bash
sudo ./uninstall.sh
```

## Logs & Debugging
The service logs its actions (start, error detection, fixes) to:
`/var/log/ntfs-auto-fix.log`

You can inspect it with:
```bash
sudo cat /var/log/ntfs-auto-fix.log
```

## Requirements
- `python3`
- `ntfs-3g` (usually pre-installed on most distros dealing with NTFS)
- `systemd` (standard init system on Arch, Ubuntu, Fedora, etc.)
- `libnotify` (for notifications)