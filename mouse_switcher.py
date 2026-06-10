import ctypes
from ctypes import wintypes
import time
import sys
from pynput import keyboard

# Ensure process DPI awareness to align Windows API coordinates with screen coordinates
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# Win32 API structures
class RECT(ctypes.Structure):
    _fields_ = [("left", wintypes.LONG), ("top", wintypes.LONG),
                ("right", wintypes.LONG), ("bottom", wintypes.LONG)]

class MONITORINFOEXW(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD),
                ("rcMonitor", RECT),
                ("rcWork", RECT),
                ("dwFlags", wintypes.DWORD),
                ("szDevice", wintypes.WCHAR * 32)]

class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]

MonitorEnumProc = ctypes.WINFUNCTYPE(
    wintypes.BOOL, wintypes.HMONITOR, wintypes.HDC, ctypes.POINTER(RECT), wintypes.LPARAM
)

def get_monitors():
    """Queries and returns a sorted list of monitor bounding rects."""
    monitors = []
    
    def monitor_callback(hMonitor, hdc, lprect, lparam):
        info = MONITORINFOEXW()
        info.cbSize = ctypes.sizeof(MONITORINFOEXW)
        if ctypes.windll.user32.GetMonitorInfoW(hMonitor, ctypes.byref(info)):
            monitors.append((
                info.rcMonitor.left,
                info.rcMonitor.top,
                info.rcMonitor.right,
                info.rcMonitor.bottom,
                info.szDevice
            ))
        return True
        
    callback = MonitorEnumProc(monitor_callback)
    ctypes.windll.user32.EnumDisplayMonitors(None, None, callback, 0)
    # Sort monitors by their left coordinate (left-to-right order)
    monitors.sort(key=lambda r: r[0])
    return monitors

def get_cursor_pos():
    """Returns the current mouse cursor (x, y) coordinates."""
    pt = POINT()
    if ctypes.windll.user32.GetCursorPos(ctypes.byref(pt)):
        return pt.x, pt.y
    return 0, 0

def set_cursor_pos(x, y):
    """Sets the cursor position to (x, y)."""
    ctypes.windll.user32.SetCursorPos(int(x), int(y))

# Keyboard listening state variables
ctrl_pressed_time = 0.0
other_key_pressed = False

def switch_screen():
    """Moves the cursor to the next screen in the monitor list."""
    monitors = get_monitors()
    if not monitors:
        print("[!] No monitors detected.", flush=True)
        return

    if len(monitors) == 1:
        # Warp to the center of the single screen
        x, y = get_cursor_pos()
        left, top, right, bottom, name = monitors[0]
        cx = (left + right) // 2
        cy = (top + bottom) // 2
        set_cursor_pos(cx, cy)
        print(f"[*] Single screen detected. Warping cursor to center: ({cx}, {cy})", flush=True)
        return

    x, y = get_cursor_pos()
    
    # Identify which monitor currently contains the cursor
    current_idx = -1
    for i, (left, top, right, bottom, name) in enumerate(monitors):
        if left <= x <= right and top <= y <= bottom:
            current_idx = i
            break
            
    # Default to monitor 0 if cursor is outside all defined boundaries (edge case)
    if current_idx == -1:
        current_idx = 0

    # Determine the next monitor index
    next_idx = (current_idx + 1) % len(monitors)
    left, top, right, bottom, name = monitors[next_idx]
    
    # Calculate the center coordinate of the next monitor
    cx = (left + right) // 2
    cy = (top + bottom) // 2
    
    # Perform the switch
    set_cursor_pos(cx, cy)
    print(f"[+] Switched mouse: Monitor {current_idx} -> Monitor {next_idx} ({name}) at ({cx}, {cy})", flush=True)

def on_press(key):
    global ctrl_pressed_time, other_key_pressed
    if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
        if ctrl_pressed_time == 0.0:
            ctrl_pressed_time = time.time()
            other_key_pressed = False
    else:
        # Any other key pressed while Ctrl is down prevents the tap action
        if ctrl_pressed_time > 0.0:
            other_key_pressed = True

def on_release(key):
    global ctrl_pressed_time, other_key_pressed
    if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
        if ctrl_pressed_time > 0.0 and not other_key_pressed:
            duration = time.time() - ctrl_pressed_time
            # A tap is defined as pressing and releasing CTRL in under 400ms without other keys
            if duration < 0.400:
                switch_screen()
        # Reset tracking state
        ctrl_pressed_time = 0.0
        other_key_pressed = False

def main():
    print("==================================================", flush=True)
    print("           WINDOWS MOUSE SCREEN SWITCHER          ", flush=True)
    print("==================================================", flush=True)
    print("How it works:", flush=True)
    print(" - Tap the 'CTRL' key (Left or Right) to switch the mouse", flush=True)
    print("   cursor to the center of the next screen.", flush=True)
    print(" - Pressing CTRL combinations (e.g., Ctrl+C, Ctrl+V, etc.)", flush=True)
    print("   will NOT trigger the switch.", flush=True)
    print(" - Press Ctrl+C in this terminal window to stop this script.", flush=True)
    print("--------------------------------------------------", flush=True)
    
    # Print monitor setup on start
    monitors = get_monitors()
    print(f"Detected {len(monitors)} monitor(s):", flush=True)
    for i, (left, top, right, bottom, name) in enumerate(monitors):
        print(f"  Monitor {i}: {name} | Bounding Rect: left={left}, top={top}, right={right}, bottom={bottom}", flush=True)
    print("--------------------------------------------------", flush=True)
    print("[*] Listening for 'CTRL' taps... (Script is active)", flush=True)

    # Start the keyboard hook listener
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        try:
            listener.join()
        except KeyboardInterrupt:
            print("\n[-] Exiting mouse switcher script. Goodbye!", flush=True)

if __name__ == "__main__":
    main()
