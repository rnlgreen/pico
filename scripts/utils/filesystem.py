"""File system utility functions"""
import uos # type: ignore # pylint: disable=import-error

def file_exists(filename):
    """Function to test if a file exists"""
    try:
        return (uos.stat(filename)[0] & 0x4000) == 0
    except OSError:
        return False

def dir_exists(foldername):
    """Function to test if a folder exists"""
    try:
        return (uos.stat(foldername)[0] & 0x8000) == 0
    except OSError:
        return False
