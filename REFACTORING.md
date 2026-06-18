# Main.py Refactoring Documentation

## Overview

The main.py file has been refactored to be more streamlined, robust, and maintainable. The file has been reduced from **242 lines to ~115 lines** by moving functionality into focused utility modules.

## New Utility Modules

### 1. `utils/config.py`
**Purpose:** Centralized configuration constants

**Contents:**
- `TESTMODE` - Test mode flag
- `EXCEPTION_FILE` - Exception log filename

**Usage:**
```python
from utils.config import TESTMODE, EXCEPTION_FILE
```

### 2. `utils/filesystem.py`
**Purpose:** File system utility functions

**Functions:**
- `file_exists(filename)` - Check if a file exists
- `dir_exists(foldername)` - Check if a directory exists

**Usage:**
```python
from utils.filesystem import file_exists, dir_exists

if file_exists("myfile.txt"):
    print("File exists")
```

### 3. `utils/status.py` (Enhanced)
**Purpose:** System status reporting (enhanced with version logging)

**New Functions:**
- `log_versions()` - Log MicroPython version information

**Existing Functions:**
- `read_internal_temperature()` - Get CPU temperature
- `fs_stats()` - Get filesystem statistics

### 4. `utils/log.py` (Enhanced)
**Purpose:** Logging and exception management (enhanced with upload/clear functions)

**New Functions:**
- `upload_exceptions()` - Upload exception log via FTP
- `clear_log(pico)` - Clear the exception log

**Existing Functions:**
- `status()`, `debug()`, `log()`, `log_exception()`, `restart_reason()`, `prune_log()`

### 5. `utils/commands.py` ⭐ NEW
**Purpose:** MQTT command handling with extensible registry pattern

**Key Features:**
- Command registry pattern for easy extension
- Separates command handling from main.py
- Support for custom topic handlers

**Built-in Commands:**
- `blink` - Blink LED
- `restart` - Restart the pico
- `datetime` - Report current time
- `uptime` - Report uptime
- `temperature` - Report CPU temperature
- `clear` - Clear exception log
- `status` - Report full status

**Usage:**
```python
from utils import commands

# Register a custom command
def handle_my_command(pico, timeInit):
    print("Custom command executed")

commands.register_command("mycommand", handle_my_command)

# Register a custom topic handler
def handle_my_topic(topic, payload):
    print(f"Custom topic: {topic}")

commands.register_topic_handler("pico/mytopic", handle_my_topic)

# Process messages (called by main.py)
commands.process_message(topic, payload, pico, timeInit, main_module)
```

### 6. `utils/init.py` ⭐ NEW
**Purpose:** Initialization sequence coordination

**Key Features:**
- Encapsulates entire startup sequence
- Returns `InitializationResult` object with status
- Error handling built-in

**Functions:**
- `initialize(pico, mp_release, callback, testmode)` - Run full initialization
- `connect_wifi(pico)` - Connect to WiFi with error handling
- `sync_ntp()` - Synchronize time
- `connect_mqtt(pico)` - Connect to MQTT broker
- `check_for_updates(pico)` - Check and apply updates
- `setup_subscriptions(pico, callback)` - Subscribe to MQTT topics

**InitializationResult Class:**
```python
class InitializationResult:
    ipaddr: str|bool           # IP address or False
    ntp_sync: bool             # NTP sync successful
    timeInit: int              # Initial timestamp
    standalone: bool           # Standalone mode flag
    mp_release: str            # MicroPython release version
    success: bool              # Overall initialization success
    init_duration_ms: int      # Time taken for initialization (milliseconds)
```

**Note:** The `init_duration_ms` field uses `time.ticks_ms()` and `time.ticks_diff()` to accurately measure initialization time, even though the system clock starts at 2021-01-01 00:00:00 before NTP sync. This ensures accurate timing regardless of when NTP synchronization occurs during the initialization process.

**Usage:**
```python
from utils.init import initialize

def on_message(topic, payload):
    # Your message handler
    pass

init_result = initialize(pico, mp_release, on_message, testmode=False)

if init_result.success:
    print(f"Initialized with IP: {init_result.ipaddr}")
    print(f"Time synced: {init_result.ntp_sync}")
    print(f"Standalone: {init_result.standalone}")
```

## Refactored main.py Structure

The new main.py follows a clean, linear structure:

```
1. Imports (focused imports from utils)
2. Startup Sequence
   - Blink LED
   - Get pico ID
   - Log versions
   - Create message handler
   - Run initialization
3. Main Execution
   - Load pico-specific module
   - Report status
   - Call module's main()
   - Handle exceptions
4. Fallback (should never reach)
```

## Benefits of Refactoring

### 1. **Cleaner main.py**
- Reduced from 242 to ~115 lines (52% reduction)
- Easier to read and understand
- Clear separation of concerns

### 2. **Better Error Handling**
- Initialization errors handled in one place
- Clear error propagation
- No more `main` used before assignment issues

### 3. **More Testable**
- Each utility module can be tested independently
- Mock initialization results easily
- Command handlers can be unit tested

### 4. **More Maintainable**
- Changes to commands don't require editing main.py
- Initialization logic centralized
- File operations in one place

### 5. **More Extensible**
- Easy to add new commands via registry
- Custom topic handlers supported
- Pico-specific modules can register their own handlers

### 6. **More Reusable**
- Utils can be used by other scripts
- Clear module interfaces
- No circular dependencies

## Migration Guide

### For Existing Pico Modules (pico0.py, pico1.py, etc.)

**No changes required!** Your existing pico modules will work as-is. However, you can optionally enhance them:

#### Optional Enhancement: Register Custom Commands

```python
# At the top of your picoX.py
from utils import commands

def my_custom_command(pico, timeInit):
    # Your custom command logic
    pass

# Register it
commands.register_command("mycmd", my_custom_command)

def main():
    # Your existing main code
    pass
```

#### Optional Enhancement: Register Custom Topics

```python
from utils import commands

def handle_my_topic(topic, payload):
    # Handle custom topic
    pass

# Register it
commands.register_topic_handler("pico/mytopic", handle_my_topic)
```

### For New Development

When creating new pico modules, you can leverage the new utilities:

```python
"""Main routine for picoX"""
from utils import mqtt
from utils import log
from utils import commands
from utils.filesystem import file_exists

# Register any custom commands for this pico
def my_command(pico, timeInit):
    log.status("Custom command executed")

commands.register_command("custom", my_command)

def get_status():
    """Called by the 'status' command"""
    log.status("My custom status info")

def led_control(topic, payload):
    """Called for LED control topics"""
    pass

def main(standalone=False):
    """Main entry point - called by main.py"""
    log.status("Starting picoX")
    
    # Your initialization code
    
    # Main loop
    while True:
        if mqtt.client is not False:
            mqtt.client.check_msg()
        # Your loop code
```

## Backward Compatibility

The refactoring maintains **100% backward compatibility**:

- All existing pico modules work without changes
- MQTT message format unchanged
- Behavior is identical to original implementation
- All commands work the same way

## Testing

After deploying the refactored code:

1. **Test MQTT Commands:**
   - Send `blink` command: `mosquitto_pub -h mqtt_server -t "pico/picoX/control" -m "blink"`
   - Send `status` command
   - Send `restart` command
   - Send `uptime` command

2. **Test Initialization:**
   - Monitor restart behavior
   - Check WiFi connection
   - Verify MQTT subscriptions
   - Confirm update checking

3. **Test Error Handling:**
   - Disconnect WiFi and observe behavior
   - Check exception logging
   - Verify FTP upload of logs

## File Structure Summary

```
scripts/
├── main.py                    (Refactored - 115 lines)
├── pico0.py - pico10.py      (Unchanged)
└── utils/
    ├── config.py             (NEW - Configuration)
    ├── filesystem.py         (NEW - File operations)
    ├── commands.py           (NEW - MQTT command handling)
    ├── init.py               (NEW - Initialization sequence)
    ├── status.py             (ENHANCED - Added log_versions)
    ├── log.py                (ENHANCED - Added upload/clear)
    └── [other existing utils]
```

## Performance Impact

- **Memory:** Minimal increase (new modules are small)
- **Startup Time:** Identical (same operations, just reorganized)
- **Runtime:** No change (same logic, better organized)

## Future Enhancements

The new structure enables easy future improvements:

1. **Dynamic Command Loading:** Load commands from config files
2. **Plugin System:** Drop-in command handlers
3. **Web Interface:** Use command registry for web API
4. **Testing Framework:** Unit tests for each util module
5. **Configuration Files:** Move more config to utils/config.py
6. **Monitoring:** Centralized health checks via status.py
