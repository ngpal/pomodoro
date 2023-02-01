import os
import pickle
import re
import time
from dataclasses import dataclass, field
from datetime import date
from sys import argv

from rich.console import Console
from rich.progress import BarColumn, Progress, TextColumn, TimeRemainingColumn

BAR_WIDTH = 50
F_DEFAULT = 20
R_DEFAULT = 5
PATH = f"{os.path.realpath(os.path.dirname(__file__))}"
DING = f"{PATH}/ding.mp3"
DATE = str(date.today())

console = Console(highlight=False)


class DailyStat:
    def __init__(self):
        self.reset()

    def reset(self):
        self.total_time_focused = 0
        self.total_time_rested = 0
        self.focus_sessions_completed = 0
        self.rest_sessions_completed = 0


try:
    with open(f"{PATH}/.pomo/stats.dat", "rb+") as f:
        stat = pickle.load(f)
except EOFError:
    stat = {}
except FileNotFoundError:
    os.system(f"mkdir {PATH}/.pomo/")
    open(f"{PATH}/.pomo/stats.dat", "w").close()
    stat = {}


@dataclass
class Help:
    desc: str
    usage: str
    examples: list[str]
    commands: list[tuple[str, str]] = field(default_factory=list)
    flags: list[tuple[str, str]] = field(default_factory=list)

    def __repr__(self) -> str:
        self.flags.append(("--help", "shows this message"))

        commands = "".join([f"    {x}\t: {y}\n" for x, y in self.commands])[:-1]
        flags = "".join([f"    {x}\t: {y}\n" for x, y in self.flags])[:-1]
        examples = "".join(f"    $ {e}\n" for e in self.examples)[:-1]

        with open(f"{PATH}/help_template.txt") as f:
            template = f.read()

        template = template.replace("{desc}", self.desc)
        template = template.replace("{usage}", self.usage)
        template = template.replace("{examples}", examples)
        template = template.replace("{commands}", commands if self.commands else "\t-")
        template = template.replace("{flags}", flags if self.flags else "\t-")

        return template


def help(command=None):
    match command:
        case "focus":
            h = Help(
                "Starts a focus mode session with default time if none given.",
                "python3 pomo.py focus \\[time] \\[flags]",
                ["python3 pomo.py focus 20 -q"],
                flags=[("--quiet", "disables ding when timer ends")],
            )

        case "rest":
            h = Help(
                "Starts a rest mode session with default time if none given.",
                "python3 pomo.py rest \\[time] \\[flags]",
                ["python3 pomo.py rest 20 -q"],
                flags=[("--quiet", "disables ding when timer ends")],
            )

        case "stats":
            h = Help(
                "Shows you the days stats.",
                "python3 pomo.py stats",
                [
                    "python3 pomo.py stats",
                ],
            )

        case _:
            h = Help(
                "Become more productive right from the command line.",
                "python3 pomo.py <command> \\[flags]",
                [
                    "python3 pomo.py focus 12",
                    "python3 pomo.py rest -q",
                    "python3 pomo.py stats",
                ],
                [
                    ("focus", "start a focus session"),
                    ("rest", "start a rest session"),
                    ("stats", "see your stats"),
                ],
            )

    console.print(repr(h))


def ding():
    os.system(f"mpg123 {DING} -q")


def save_data(data):
    stat[DATE] = data
    with open(f"{PATH}/.pomo/stats.dat", "wb") as f:
        pickle.dump(stat, f)


def parse_args(args: str) -> list:
    args_list = args.split()
    if re.match(r"^(focus|rest|stats)$", args):
        return [args_list[0], None, None]
    elif re.match(r"^(focus|rest)\s+([1-9]|[1-9][0-9]|[1-9][0-9][0-9])", args):
        return [args_list[0], int(args_list[1]), None]
    elif re.match(r"^(focus|rest|stats)\s+(\-(h|q)|\-\-(help|quiet))", args):
        return [args_list[0], None, args_list[1]]
    elif re.match(
        r"^(focus|rest)\s+([1-9]|[1-9][0-9]|[1-9][0-9][0-9])\s+(\-(h|q)|\-\-(help|quiet))",
        args,
    ):
        return [args_list[0], int(args_list[1]), args_list[2]]
    return [None, None, None]


def render_timer(command: str, dur: int, flag: str):
    command = command.title()
    if command == "Focus":
        color = "green"
    else:
        color = "magenta"

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(
            complete_style=color,
            style="bright_black",
            bar_width=BAR_WIDTH,
        ),
        TimeRemainingColumn(),
    ) as progress:

        timer = progress.add_task(f"[yellow] {command}", total=dur * 60)
        while not progress.finished:
            progress.update(timer, advance=1)
            time.sleep(1)

    if command == "Focus":
        t_stat.total_time_focused += dur
        t_stat.focus_sessions_completed += 1
    else:
        t_stat.total_time_rested += dur
        t_stat.rest_sessions_completed += 1

    save_data(t_stat)
    console.print("[green b] Session complete!")

    if flag not in ["-q", "--quiet"]:
        ding()


t_stat = stat.get(DATE, DailyStat())

args = argv[1:4]
if not args or args[0] in ["-h", "--help"]:
    help()
    quit()

match parse_args(" ".join(args)):
    case "focus", dur, flag:
        if flag in ["-h", "--help"]:
            help("focus")
            quit()

        if not dur:
            dur = F_DEFAULT

        render_timer("focus", dur, flag)

    case "rest", dur, flag:
        if flag in ["-h", "--help"]:
            help("rest")
            quit()

        if not dur:
            dur = R_DEFAULT

        render_timer("rest", dur, flag)

    case "stats", _, flag:
        if flag in ["-h", "--help"]:
            help("stats")
            quit()

        console.print(f"[yellow b u]TODAY'S STATS\n")
        console.print(f"Total time focused                 {t_stat.total_time_focused}")
        console.print(f"Total time rested                  {t_stat.total_time_rested}")
        console.print(
            f"Focus sessions completed           {t_stat.focus_sessions_completed}"
        )
        console.print(
            f"Rest sessions completed            {t_stat.rest_sessions_completed}"
        )

    case _:
        console.print("Invalid syntax. Use [b]python3 pomo.py -h[/] for help")
