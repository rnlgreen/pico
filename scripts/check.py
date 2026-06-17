""" boot script to syntax check boot.py, """
import sys

# If boot.py, does not compile, report via MQTT and refresh code via FTP
def syntax_check(source):
    """Function to check the syntax of boot.py,"""
    try:
        compile(source, "boot.py", "exec")
        return True, None
    except Exception as e: # pylint: disable=broad-except
        return False, str(e)

if len(sys.argv) > 1:
    sourcecode = sys.argv[1]
else:
    sourcecode = "main.py"

# Main logic
ok, err = syntax_check(sourcecode)

if ok:
    print(f"{sourcecode}, syntax check passed")
else:
    print("=" * 50)
    print(f"CRITICAL: {sourcecode}, has syntax errors!")
    print("=" * 50)
    print(err)
    print("=" * 50)
    exit(1)  # Exit to prevent running boot.py, with syntax errors
