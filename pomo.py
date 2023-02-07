import os

from src import cli

try:
    os.chdir(f"{os.path.realpath(os.path.dirname(__file__))}")
except:
    print("Unexpected error occured. (os.chdir)")
    quit()

__all__ = ["cli"]
