import os
from sys import argv

from src import CommandManager

try:
    os.chdir(f"{os.path.realpath(os.path.dirname(__file__))}")
except:
    print("Unexpected error occured. (os.chdir)")
    quit()


def main():
    CommandManager().execute_cmd(argv[1:4])
