# Safe Update Quick Start Guide

## TL;DR - The Problem and Solution

**Problem**: Using `boot.py` to catch and fix bad updates can brick your Pico if `boot.py` itself fails.

**Solution**: Move syntax checking into the update process itself, so bad files are caught and rolled back BEFORE they can cause problems.

## Quick Migration Steps

### Step 1: Update update.py (✓ Already Done)
The enhanced `update.py` now automatically:
- Backs up critical files before updating
- Checks syntax after downloading
- Rolls back if errors detected

### Step 2: Choose Your Boot Strategy

**Option A - No boot.py (Safest)**
```bash
# Simply delete or rename boot.py
# Let MicroPython boot directly to main.py
```

**Option B - Minimal boot.py (Safe)**
```bash
# Copy boot_minimal.py to boot.py
# Reports errors but doesn't prevent boot
```

### Step 3: Create Initial Backups
```python
from utils import update
update.manual_backup('main.py')
update.manual_backup('pico0.py')  # Your specific pico file
```

### Step 4: Configure Critical Files
Edit `utils/update.py` line 9:
```python
CRITICAL_FILES = ['main.py', 'pico0.py']  # Add your pico's file
```

## How to Use

### Normal Update (Automatic Safety)
```python
from utils import update
result = update.update()
# Automatically backs up, checks syntax, and rolls back if needed
```

### Check Return Value
```python
result = update.update()

if result < 0:
    # Syntax errors detected and rolled back
    print(f"Rolled back {abs(result)} file(s)")
elif result > 0:
    # Success
    print(f"Updated {result} file(s)")
else:
    # No updates needed
    print("Already up to date")
```

### Manual Restore (Emergency)
```python
from utils import update
update.manual_restore('main.py')
```

### Syntax Check Only
```python
from utils import update
is_valid, error = update.check_file_syntax('main.py')
print(f"Valid: {is_valid}")
if not is_valid:
    print(error)
```

## Key Benefits

✓ **Self-Healing**: Bad files detected and rolled back automatically  
✓ **No Bricking**: Update process can't brick your device  
✓ **Logged**: All errors logged via MQTT for remote monitoring  
✓ **Manual Override**: Can manually backup/restore if needed  
✓ **Backward Compatible**: Works with existing update workflow  

## Files Created

- `utils/update.py` - Enhanced with backup/syntax check/rollback
- `scripts/boot_minimal.py` - Minimal safe boot option
- `SAFE_UPDATE_APPROACH.md` - Detailed documentation
- `SAFE_UPDATE_QUICKSTART.md` - This file
- `utils/update_example.py` - Usage examples

## What Changed in update.py

### New Functions
- `syntax_check(filepath)` - Check Python syntax
- `backup_file(filepath)` - Create .backup copy
- `restore_backup(filepath)` - Restore from backup
- `verify_and_rollback_if_needed(filepath)` - Check & rollback
- `manual_backup(filepath)` - Manual backup wrapper
- `manual_restore(filepath)` - Manual restore wrapper
- `check_file_syntax(filepath)` - Manual syntax check wrapper

### Enhanced update() Function
```python
def update(cleanup=False, skip_syntax_check=False):
    # Now includes:
    # 1. Backup critical files before update
    # 2. Download files as before
    # 3. Check syntax of critical files
    # 4. Rollback if errors detected
    # 5. Return negative on errors, positive on success
```

## Testing on One Pico First

1. Upload new `update.py` via Thonny/FTP
2. Connect via Thonny REPL
3. Run: `from utils import update; update.manual_backup('main.py')`
4. Run: `result = update.update()`
5. Check result and logs
6. If successful, roll out to other Picos

## Monitoring

All operations are logged via MQTT:
- Backup creation: "Backed up X to X.backup"
- Syntax errors: "SYNTAX ERROR in X!"
- Rollbacks: "Successfully rolled back X"
- Critical failures: "CRITICAL: Could not restore X"

## Additional Safety Tips

1. **Test locally first**: `python -m py_compile main.py`
2. **Use git tags**: Tag stable versions
3. **Gradual rollout**: Test on one Pico, wait 24h, then deploy
4. **Keep FTP backup**: Don't delete old versions immediately
5. **Monitor logs**: Watch MQTT for update messages

## Backward Compatibility

The enhanced `update.update()` is backward compatible:
- Same parameters as before
- Returns same positive values on success
- Only new behavior: returns negative on syntax errors

Existing code calling `update.update()` will continue to work.

## Need Help?

See detailed documentation in `SAFE_UPDATE_APPROACH.md`
See code examples in `utils/update_example.py`
