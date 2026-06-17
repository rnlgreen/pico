""" boot script to syntax check main.py """
# If main.py does not compile, report via MQTT and refresh code via FTP
def syntax_check():
    """Function to check the syntax of main.py"""
    try:
        with open("main.py", "r") as f: # pylint: disable=unspecified-encoding
            code = f.read()
        compile(code, "main.py", "exec")
        return True, None
    except Exception as e: # pylint: disable=broad-except
        return False, str(e)

# Main logic
ok, err = syntax_check()

if ok:
    print("main.py syntax check passed")
else:
    print("=" * 50)
    print("CRITICAL: main.py has syntax errors!")
    print("=" * 50)
    print(err)
    print("=" * 50)
    exit(1)  # Exit to prevent running main.py with syntax errors

# If syntax check passed, continue to main.py normally
print("Boot complete, loading main.py...")
