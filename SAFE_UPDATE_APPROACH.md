# Safe Update Approach for Raspberry Pi Pico

## Problem Statement

Using `boot.py` for syntax checking and automatic FTP recovery creates a risk:
- If `boot.py` itself fails, the Pico can become essentially bricked
- Even USB drivers may fail to load
- Requires using `nuke___.uf2` to completely reset the device

## Solution: Backup and Syntax Check in update.py

Instead of relying on `boot.py` to catch and fix problems, the update process itself now handles:
1. **Automatic Backup**: Before downloading new versions of critical files
2. **Syntax Checking**: Verification of Python syntax after download
3. **Automatic Rollback**: If syntax errors are detected, restore the backup

## How It Works

### Enhanced update.py Features

The updated `update.py` now includes:

1. **Critical Files List**: Define which files should be backed up
   ```python
   CRITICAL_FILES = ['main.py']  # Add more as needed
   ```

2. **Automatic Backup Before Update**:
   - Before downloading any files, creates `.backup` copies of critical files
   - Example: `main.py` → `main.py.backup`

3. **Syntax Checking After Update**:
   - Uses Python's `compile()` to verify syntax
   - Runs automatically after updating critical files
   - Can be skipped with `skip_syntax_check=True` parameter (not recommended)

4. **Automatic Rollback**:
   - If syntax errors detected, restores from backup
   - Logs the error for debugging
   - Returns negative number to indicate errors occurred

### New Functions Available

```python
# Main update function (enhanced)
result = update.update(cleanup=False, skip_syntax_check=False)
# Returns: positive = files updated successfully
#          0 = no updates needed
#          negative = syntax errors occurred (and rolled back)

# Manual operations
from utils import update

# Manually backup a file
update.manual_backup('main.py')

# Manually restore from backup
update.manual_restore('main.py')

# Check syntax without rollback
is_valid, error_msg = update.check_file_syntax('main.py')
```

## Boot.py Options

### Option 1: No boot.py (Recommended)
Simply don't use `boot.py` at all. Let MicroPython boot directly to `main.py`.

**Pros:**
- No risk of boot.py bricking the device
- Simpler system
- Syntax errors caught by update process

**Cons:**
- If a bad main.py somehow gets on the device, it will fail at runtime

### Option 2: Minimal boot.py (Included as boot_minimal.py)
Use the minimal `boot_minimal.py` that only checks syntax and reports errors, but doesn't prevent boot.

**Pros:**
- Early warning of syntax errors
- No network operations that could fail
- Won't brick the device

**Cons:**
- Doesn't prevent failed boot, just reports it

### Option 3: Keep current boot.py (Not Recommended)
The current `boot.py` does network recovery but has bricking risk.

## Recommended Workflow

### Initial Setup

1. **Create Initial Backups**:
   ```python
   from utils import update
   update.manual_backup('main.py')
   # Backup any pico-specific files too
   update.manual_backup('pico0.py')  # etc.
   ```

2. **Add Pico-Specific Files to CRITICAL_FILES**:
   Edit `update.py` to include your pico's specific file:
   ```python
   CRITICAL_FILES = ['main.py', 'pico0.py']  # or pico1.py, etc.
   ```

### Regular Updates

When you run an update:
```python
from utils import update
result = update.update()

if result < 0:
    print("Update had syntax errors - files were rolled back")
elif result > 0:
    print(f"Successfully updated {result} files")
else:
    print("No updates available")
```

### Emergency Recovery

If you need to manually restore a file:
```python
from utils import update
update.manual_restore('main.py')
```

### Testing Before Deployment

Before pushing to FTP server:
1. Test syntax locally: `python -m py_compile main.py`
2. Run pylint to catch issues
3. Consider a staging Pico for testing updates

## Additional Safety Measures

### 1. Version Control
Keep your code in git and tag stable versions:
```bash
git tag -a v1.0 -m "Stable version"
```

### 2. Gradual Rollout
- Test updates on one Pico first
- Monitor for 24 hours
- Then deploy to others

### 3. Remote Backup Command
Add an MQTT command to trigger manual backups:
```python
# In your MQTT command handler
if command == "backup":
    from utils import update
    update.manual_backup('main.py')
```

### 4. Health Check Command
Add an MQTT command to check file integrity:
```python
if command == "check":
    from utils import update
    is_valid, error = update.check_file_syntax('main.py')
    log.status(f"main.py valid: {is_valid}", logit=True)
```

## File Structure After Update

Your Pico will have:
```
/
├── main.py              # Current version
├── main.py.backup       # Previous working version
├── pico0.py             # Your specific pico file
├── pico0.py.backup      # Backup of specific file
├── boot.py              # (optional) minimal boot checker
├── utils/
│   ├── update.py        # Enhanced update system
│   └── ...
└── ...
```

## Migration from Current System

1. **Update the update.py file** (already done)
2. **Test on one Pico**:
   - Upload new `update.py` manually via FTP/Thonny
   - Create initial backups
   - Run an update test
3. **Choose boot.py approach**:
   - Remove `boot.py` entirely, OR
   - Replace with `boot_minimal.py`
4. **Roll out to other Picos** once tested

## Summary

**Key Advantage**: The update process itself is self-healing. If a bad file is downloaded, it's automatically detected and rolled back BEFORE the device reboots. This means you never end up with a non-bootable system that requires physical access to fix.

**Safety First**: By moving syntax checking into the update process rather than boot process, we eliminate the risk of boot.py failures bricking the device.
