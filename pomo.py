import os
import re
from sys import argv

from src import RenderManager, StatManager

F_DEFAULT = 20
R_DEFAULT = 5


try:
    os.chdir(f"{os.path.realpath(os.path.dirname(__file__))}")
except:
    print("Unexpected error occured. (os.chdir)")
    quit()

DING = f"./ding.mp3"

FLAGS = r"(\-(h|q|s)|\-\-(help|quiet|stopwatch))"
NUMS = r"([1-9]|[1-9][0-9]|[1-9][0-9][0-9])"
ARG_PATTERS = {
    "cmd": re.compile(r"^(focus|rest|stats)$"),
    "cmd dur": re.compile(rf"^(focus|rest)\s+{NUMS}"),
    "cmd flag": re.compile(rf"^(focus|rest)\s+{FLAGS}"),
    "stats flag": re.compile(r"^(stats)\s+(\-(h|g)|\-\-(help|graph))"),
    "cmd dur flag": re.compile(rf"^(focus|rest)\s+{NUMS}\s+{FLAGS}"),
}


stats = StatManager()
rm = RenderManager()


def parse_args(args: str) -> list:
    args_list = args.split()
    if ARG_PATTERS["cmd"].match(args):
        return [args_list[0], None, None]
    elif ARG_PATTERS["cmd dur"].match(args):
        return [args_list[0], int(args_list[1]), None]
    elif ARG_PATTERS["cmd flag"].match(args):
        return [args_list[0], None, args_list[1]]
    elif ARG_PATTERS["stats flag"].match(args):
        return ["stats", None, args_list[1]]
    elif ARG_PATTERS["cmd dur flag"].match(args):
        return [args_list[0], int(args_list[1]), args_list[2]]
    return [None, None, None]


args = argv[1:4]
if not args or args[0] in ["-h", "--help"]:
    rm.render_help()
    quit()

match parse_args(" ".join(args)):
    case cmd, _, flag if flag in ["-h", "--help"]:
        rm.render_help(cmd)

    case "focus", dur, flag:
        if flag in ["-s", "--stopwatch"]:
            t = rm.render_stopwatch("[yellow]Focus[/]")
        else:
            t = rm.render_timer("focus", dur or F_DEFAULT, flag)

        stats.update_focus(t)

    case "rest", dur, flag:
        if flag in ["-s", "--stopwatch"]:
            t = rm.render_stopwatch("[yellow]Rest[/]")
        else:
            t = rm.render_timer("rest", dur or R_DEFAULT, flag)

        stats.update_rest(t)

    case "stats", _, flag:
        if flag in ["-g", "--graph"]:
            rm.render_graph()
        else:
            rm.render_stats()

    case _:
        rm.console.print("Invalid syntax. Use [b]python3 pomo.py -h[/] for help")
