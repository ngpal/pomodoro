import os
import pickle
import re
import time
from dataclasses import dataclass, field
from datetime import date
from itertools import cycle
from sys import argv

from rich.console import Console
from rich.progress import BarColumn, Progress, TextColumn, TimeRemainingColumn

BAR_WIDTH = 50
F_DEFAULT = 20
R_DEFAULT = 5
SPIN = cycle(["⡇", "⠏", "⠛", "⠹", "⢸", "⣰", "⣤", "⣆"])
PATH = f"{os.path.realpath(os.path.dirname(__file__))}"
DING = f"{PATH}/ding.mp3"
DATE = str(date.today())

FLAGS = r"(\-(h|q|s)|\-\-(help|quiet|stopwatch))"
NUMS = r"([1-9]|[1-9][0-9]|[1-9][0-9][0-9])"
ARG_PATTERS = {
    "cmd": re.compile(r"^(focus|rest|stats)$"),
    "cmd dur": re.compile(rf"^(focus|rest)\s+{NUMS}"),
    "cmd flag": re.compile(rf"^(focus|rest)\s+{FLAGS}"),
    "stats help": re.compile(r"^(stats)\s+(\-h|\-\-help)"),
    "cmd dur flag": re.compile(rf"^(focus|rest)\s+{NUMS}\s+{FLAGS}"),
}

hide_cursor = lambda: print("\033[?25l", end="")
show_cursor = lambda: print("\033[?25h", end="")
console = Console(highlight=False)


class DailyStat:
    def __init__(self):
        self.reset()

    def reset(self):
        self.total_time_focused = 0
        self.total_time_rested = 0
        self.focus_sessions_completed = 0
        self.rest_sessions_completed = 0

    def update_focus(self, dur: int):
        self.total_time_focused += dur
        self.focus_sessions_completed += 1

    def update_rest(self, dur: int):
        self.total_time_rested += dur
        self.rest_sessions_completed += 1


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
                flags=[
                    ("--quiet", "disables ding when timer ends"),
                    ("--stopwatch", "stopwatch mode (timer goes on indefinitely)"),
                ],
            )

        case "rest":
            h = Help(
                "Starts a rest mode session with default time if none given.",
                "python3 pomo.py rest \\[time] \\[flags]",
                ["python3 pomo.py rest 20 -q"],
                flags=[
                    ("--quiet", "disables ding when timer ends"),
                    ("--stopwatch", "stopwatch mode (timer goes on indefinitely)"),
                ],
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
                    "python3 pomo.py focus -s",
                    "python3 pomo.py rest 12 -q",
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


def get_stats():
    try:
        with open(f"{PATH}/.pomo/stats.dat", "rb+") as f:
            stat = pickle.load(f)
    except EOFError:
        stat = {}
    except FileNotFoundError:
        os.system(f"mkdir {PATH}/.pomo/")
        open(f"{PATH}/.pomo/stats.dat", "w").close()
        stat = {}

    return stat


def save_data(data):
    stat[DATE] = data
    with open(f"{PATH}/.pomo/stats.dat", "wb") as f:
        pickle.dump(stat, f)


def parse_args(args: str) -> list:
    args_list = args.split()
    if ARG_PATTERS["cmd"].match(args):
        return [args_list[0], None, None]
    elif ARG_PATTERS["cmd dur"].match(args):
        return [args_list[0], int(args_list[1]), None]
    elif ARG_PATTERS["cmd flag"].match(args):
        return [args_list[0], None, args_list[1]]
    elif ARG_PATTERS["stats help"].match(args):
        return ["stats", None, "-h"]
    elif ARG_PATTERS["cmd dur flag"].match(args):
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
        t_stat.update_focus(dur * 60)
    else:
        t_stat.update_rest(dur * 60)

    save_data(t_stat)
    console.print("[green b] Session complete!")

    if flag not in ["-q", "--quiet"]:
        ding()


def format_time(h, m, s):
    m = str(m).rjust(2, "0")
    s = str(s).rjust(2, "0")

    return f"{h}:{m}:{s}"


def render_stopwatch(text: str) -> int:
    h = m = s = 0
    w, _ = os.get_terminal_size()
    spinner = next(SPIN)
    t = 0

    try:
        hide_cursor()
        while True:
            w, _ = os.get_terminal_size()
            w = w - len(text) - 8
            m, s = divmod(t // 100, 60)
            h, m = divmod(m, 60)
            console.print(
                f"[green]{spinner}[/] {text} [cyan]{format_time(h, m, s)}",
                end=" " * w + "\r",
            )
            time.sleep(0.01)
            t += 1

            if not t % 10:
                spinner = next(SPIN)

    except KeyboardInterrupt:
        show_cursor()
        console.print(" " * w, end="\r")
        console.print(f"[red b]![/] {text} [green b]{format_time(h, m, s)}")

        return t // 100


stat = get_stats()
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

        if flag in ["-s", "--stopwatch"]:
            t = render_stopwatch("[yellow]Focus[/]")
            t_stat.update_focus(t)
            save_data(t_stat)
            quit()

        if not dur:
            dur = F_DEFAULT

        render_timer("focus", dur, flag)

    case "rest", dur, flag:
        if flag in ["-h", "--help"]:
            help("rest")
            quit()

        if flag in ["-s", "--stopwatch"]:
            t = render_stopwatch("[yellow]Rest[/]")
            t_stat.update_rest(t)
            save_data(t_stat)
            quit()

        if not dur:
            dur = R_DEFAULT

        render_timer("rest", dur, flag)

    case "stats", _, flag:
        if flag in ["-h", "--help"]:
            help("stats")
            quit()

        try:
            ratio = t_stat.total_time_focused / t_stat.total_time_rested
            if ratio > 1:
                ratio = f"[green b]{ratio:.2f}"
            else:
                ratio = f"[red b]{ratio:.2f}"
        except ZeroDivisionError:
            ratio = "[red b]No rest today"

        fm, fs = divmod(t_stat.total_time_focused, 60)
        fdat = f"[green b]{fm}[/] minutes"
        if fs:
            fdat += f" [green b]{fs}[/] seconds"

        rm, rs = divmod(t_stat.total_time_rested, 60)
        rdat = f"[magenta b]{rm}[/] minutes"
        if rs:
            rdat += f" [magenta b]{rs}[/] seconds"

        with open(f"{PATH}/stats_template.txt") as f:
            template = f.read()

        template = template.replace("{focused}", fdat)
        template = template.replace("{rested}", rdat)
        template = template.replace("{fcount}", f"{t_stat.focus_sessions_completed}")
        template = template.replace("{rcount}", f"{t_stat.rest_sessions_completed}")
        template = template.replace("{ratio}", ratio)

        console.print("[red b u]TODAY'S STATS[/]\n")
        console.print(template)

    case _:
        console.print("Invalid syntax. Use [b]python3 pomo.py -h[/] for help")
