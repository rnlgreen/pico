"""
Example usage of the enhanced update.py features
This demonstrates backup, syntax checking, and rollback functionality
"""

from utils import update
from utils import log

def example_safe_update():
    """Example: Run a safe update with automatic backup and syntax check"""
    print("\n=== Running Safe Update ===")
    
    result = update.update(cleanup=False, skip_syntax_check=False)
    
    if result < 0:
        log.status("⚠️ Update failed - syntax errors detected and rolled back", logit=True)
        print(f"Number of files with errors: {abs(result)}")
        print("Your previous working versions have been restored")
    elif result > 0:
        log.status(f"✓ Successfully updated {result} file(s)", logit=True)
        print("All syntax checks passed")
    else:
        print("No updates available")

def example_manual_backup():
    """Example: Manually create backups before risky operations"""
    print("\n=== Creating Manual Backups ===")
    
    # Backup critical files
    files_to_backup = ['main.py', 'pico0.py']  # Adjust for your pico
    
    for filepath in files_to_backup:
        if update.file_exists(filepath):
            success = update.manual_backup(filepath)
            if success:
                print(f"✓ Backed up {filepath}")
            else:
                print(f"✗ Failed to backup {filepath}")
        else:
            print(f"⚠ {filepath} not found")

def example_syntax_check():
    """Example: Check syntax of a file without making changes"""
    print("\n=== Checking File Syntax ===")
    
    files_to_check = ['main.py']
    
    for filepath in files_to_check:
        if update.file_exists(filepath):
            is_valid, error_msg = update.check_file_syntax(filepath)
            if is_valid:
                print(f"✓ {filepath} syntax is valid")
            else:
                print(f"✗ {filepath} has syntax errors:")
                print(f"   {error_msg[:200]}")
        else:
            print(f"⚠ {filepath} not found")

def example_manual_restore():
    """Example: Manually restore a file from backup"""
    print("\n=== Manual Restore Example ===")
    
    filepath = 'main.py'
    
    print(f"This would restore {filepath} from {filepath}.backup")
    print("Uncomment the line below to actually perform restore:")
    # success = update.manual_restore(filepath)
    # if success:
    #     print(f"✓ Restored {filepath} from backup")
    # else:
    #     print(f"✗ Failed to restore {filepath}")

def example_initial_setup():
    """Example: Initial setup for a new or existing pico"""
    print("\n=== Initial Setup ===")
    
    from utils import myid
    
    # Get this pico's ID
    pico_id = myid.get_id()
    print(f"Setting up {pico_id}")
    
    # Create initial backups
    critical_files = ['main.py', f'{pico_id}.py']
    
    print("\nCreating initial backups...")
    for filepath in critical_files:
        if update.file_exists(filepath):
            success = update.manual_backup(filepath)
            if success:
                print(f"  ✓ {filepath}")
            else:
                print(f"  ✗ {filepath} (backup failed)")
        else:
            print(f"  ⚠ {filepath} (not found)")
    
    print("\nNow edit update.py and add to CRITICAL_FILES:")
    print(f"  CRITICAL_FILES = ['main.py', '{pico_id}.py']")

# Usage examples:
if __name__ == "__main__":
    print("=" * 60)
    print("Enhanced Update System Examples")
    print("=" * 60)
    
    # Uncomment the example you want to run:
    
    # Most common: Run safe update
    # example_safe_update()
    
    # Initial setup
    # example_initial_setup()
    
    # Manual operations
    # example_manual_backup()
    # example_syntax_check()
    # example_manual_restore()
    
    print("\nUncomment the examples you want to run in this file")
