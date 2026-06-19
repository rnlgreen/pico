""" Minimal boot script - just checks syntax without network recovery """
# This is a safer alternative to boot.py that doesn't risk bricking the device
# It only checks syntax and reports the error, then continues to main.py anyway

def syntax_check():
    """Function to check the syntax of main.py"""
    try:
        with open("main.py", "r") as f: # pylint: disable=unspecified-encoding
            code = f.read()
        compile(code, "main.py", "exec")
        return True, None
    except Exception as e: # pylint: disable=broad-except
        import io  # pylint: disable=import-outside-toplevel
        import sys # pylint: disable=import-outside-toplevel
        output = io.StringIO()
        sys.print_exception(e, output) # pylint: disable=maybe-no-member
        e_str = output.getvalue()
        output.close()
        return False, e_str

# Check syntax but don't prevent boot
ok, err = syntax_check()

if ok:
    print("main.py syntax check passed")
else:
    print("=" * 50)
    print("WARNING: main.py has syntax errors!")
    print("=" * 50)
    print(err)
    print("=" * 50)
    print("Continuing anyway - main.py will fail when imported")

print("Boot complete, loading main.py...")
