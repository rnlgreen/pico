# Safe Update System - Documentation Index

## 📋 Quick Navigation

### For Getting Started
**→ [SAFE_UPDATE_QUICKSTART.md](SAFE_UPDATE_QUICKSTART.md)**  
Start here! Quick guide to understanding and implementing the safe update approach.

### For Understanding Why
**→ [BOOT_VS_UPDATE_COMPARISON.md](BOOT_VS_UPDATE_COMPARISON.md)**  
Detailed comparison of boot.py vs update.py approaches and risk analysis.

### For Complete Details
**→ [SAFE_UPDATE_APPROACH.md](SAFE_UPDATE_APPROACH.md)**  
Comprehensive documentation with examples, workflows, and best practices.

### For Code Examples
**→ [scripts/utils/update_example.py](scripts/utils/update_example.py)**  
Working code examples showing all features.

---

## 🎯 The Problem You Had

> "I'm faced with the possibility that boot.py fails in some way which leaves the pico essentially bricked, even USB drivers fail to load and I have to use nuke___.uf2 to totally reset the pico."

## ✅ The Solution Provided

Move syntax checking and backup/rollback functionality into the update process itself:
- **Backup** critical files before downloading updates
- **Syntax check** new files after download but BEFORE reboot  
- **Rollback** automatically if errors detected
- Device **never leaves a working state**
- **No network operations during boot** = no bricking risk

---

## 📁 Files Created

### Core Implementation
- **`scripts/utils/update.py`** - Enhanced update system (MODIFIED)
  - Automatic backup before update
  - Syntax checking after download
  - Automatic rollback on errors
  - Manual backup/restore functions

### Alternative Boot Option
- **`scripts/boot_minimal.py`** - Minimal safe boot.py (NEW)
  - Only checks syntax and reports
  - No network operations
  - Won't brick device
  - Optional to use

### Documentation
- **`SAFE_UPDATE_QUICKSTART.md`** - Quick start guide
- **`SAFE_UPDATE_APPROACH.md`** - Detailed documentation
- **`BOOT_VS_UPDATE_COMPARISON.md`** - Safety comparison
- **`SAFE_UPDATE_INDEX.md`** - This file

### Examples
- **`scripts/utils/update_example.py`** - Usage examples

---

## 🚀 Quick Implementation

### 1. Update Is Already Enhanced ✓
The `scripts/utils/update.py` has been enhanced with backup and syntax checking.

### 2. Choose Boot Strategy

**Option A: No boot.py (Recommended)**
```bash
# Delete or rename boot.py on your Pico
# Let it boot directly to main.py
```

**Option B: Minimal boot.py**
```bash
# Copy boot_minimal.py to boot.py
# Safe syntax checking without network risk
```

### 3. Create Initial Backups
```python
from utils import update
update.manual_backup('main.py')
update.manual_backup('pico0.py')  # Or your specific file
```

### 4. Configure Critical Files
Edit `scripts/utils/update.py` line 9:
```python
CRITICAL_FILES = ['main.py', 'pico0.py']  # Add your files
```

### 5. Test It!
```python
from utils import update
result = update.update()
print(f"Result: {result}")
```

---

## 🔑 Key Features

| Feature | Description |
|---------|-------------|
| **Automatic Backup** | Critical files backed up before update |
| **Syntax Checking** | Python syntax verified after download |
| **Auto Rollback** | Bad files restored from backup automatically |
| **MQTT Logging** | All operations logged for remote monitoring |
| **Manual Functions** | Backup/restore/check functions available |
| **Backward Compatible** | Works with existing update workflow |
| **No Bricking Risk** | USB access always maintained |

---

## 📊 Safety Comparison

| Aspect | boot.py | update.py |
|--------|---------|-----------|
| Bricking Risk | ❌ High | ✅ None |
| USB Access | ❌ May fail | ✅ Always works |
| Network Dependency | ❌ Required | ✅ Not required |
| Runs Every Boot | ❌ Yes (overhead) | ✅ Only on update |
| Recovery Method | ❌ Physical access | ✅ Automatic |

---

## 🛠️ New Functions Available

```python
from utils import update

# Main update with safety
result = update.update()

# Manual backup
update.manual_backup('main.py')

# Manual restore
update.manual_restore('main.py')

# Syntax check only
is_valid, error = update.check_file_syntax('main.py')
```

---

## 📖 Recommended Reading Order

1. **SAFE_UPDATE_QUICKSTART.md** - Understand the solution (5 min read)
2. **BOOT_VS_UPDATE_COMPARISON.md** - Understand the risks (10 min read)
3. **scripts/utils/update_example.py** - See code examples (5 min)
4. **SAFE_UPDATE_APPROACH.md** - Deep dive when needed (reference)

---

## ⚠️ Migration Checklist

- [ ] Read SAFE_UPDATE_QUICKSTART.md
- [ ] Test enhanced update.py on one Pico
- [ ] Create initial backups
- [ ] Configure CRITICAL_FILES in update.py
- [ ] Choose boot.py strategy (none or minimal)
- [ ] Test update process with syntax check
- [ ] Monitor MQTT logs
- [ ] Roll out to remaining Picos

---

## 💡 Best Practices

1. **Test locally first**: `python -m py_compile your_file.py`
2. **Gradual rollout**: One Pico → Wait 24h → Deploy to rest
3. **Monitor logs**: Watch MQTT for update messages
4. **Keep backups**: Don't delete old FTP versions immediately
5. **Version control**: Use git tags for stable releases

---

## 🆘 Emergency Recovery

If something goes wrong:

```python
# Via Thonny/USB REPL:
from utils import update

# Restore from backup
update.manual_restore('main.py')

# Check current syntax
is_valid, error = update.check_file_syntax('main.py')
print(f"Valid: {is_valid}")
if not is_valid:
    print(error)
```

---

## 📞 Support

- See example code: `scripts/utils/update_example.py`
- Read documentation: Files listed above
- Check current setup: Run `update.check_file_syntax('main.py')`

---

## Summary

**You asked for**: A safer alternative to boot.py that won't brick your Pico

**You received**:
- ✅ Enhanced update.py with backup/rollback
- ✅ Automatic syntax checking
- ✅ Optional minimal boot.py
- ✅ Complete documentation
- ✅ Working examples
- ✅ Migration guide

**Result**: Your Picos are now protected from bad updates without the risk of being bricked by the protection mechanism itself.
