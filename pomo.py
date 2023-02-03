import os
import re
import time
from dataclasses import dataclass, field
from itertools import cycle
from statistics import mean
from sys import argv

from dateutil import parser
from rich.console import Console
from rich.progress import BarColumn, Progress, TextColumn, TimeRemainingColumn

from src import DailyStat, StatManager

BAR_WIDTH = 50
F_DEFAULT = 20
R_DEFAULT = 5
SPIN = cycle(["⡇", "⠏", "⠛", "⠹", "⢸", "⣰", "⣤", "⣆"])
DIR = f"{os.path.realpath(os.path.dirname(__file__))}"
DING = f"{dir}/ding.mp3"

FLAGS = r"(\-(h|q|s)|\-\-(help|quiet|stopwatch))"
NUMS = r"([1-9]|[1-9][0-9]|[1-9][0-9][0-9])"
ARG_PATTERS = {
    "cmd": re.compile(r"^(focus|rest|stats)$"),
    "cmd dur": re.compile(rf"^(focus|rest)\s+{NUMS}"),
    "cmd flag": re.compile(rf"^(focus|rest)\s+{FLAGS}"),
    "stats flag": re.compile(r"^(stats)\s+(\-(h|g)|\-\-(help|graph))"),
    "cmd dur flag": re.compile(rf"^(focus|rest)\s+{NUMS}\s+{FLAGS}"),
}

hide_cursor = lambda: print("\033[?25l", end="")
show_cursor = lambda: print("\033[?25h", end="")
console = Console(highlight=False)
stats = StatManager()


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

        with open(f"{DIR}/templates/help_template.txt") as f:
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
                flags=[
                    (
                        "--graph",
                        "displays a bar graph of the F/R ratio from the past week",
                    )
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
        stats.update_focus(dur * 60)
    else:
        stats.update_rest(dur * 60)

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


def name_days(data):
    new_data = []
    if len(data):
        new_data.append(("Today".ljust(9), data[-1][1]))

    if len(data) > 1:
        new_data.append(("Yesterday", data[-2][1]))

    for date, val in data[-3:0:-1]:
        day = parser.parse(date).date().strftime("%A").ljust(9)
        new_data.append((day, val))

    return new_data[::-1]


def render_graph():
    def fr_gen(x: DailyStat):
        if not x.total_time_rested:
            return x.total_time_focused

        return x.total_time_focused / x.total_time_rested

    data = stats.get_past_data()

    if not data:
        console.print("[red b]No data!")
        quit()

    data = [(date, fr_gen(stat)) for date, stat in data]
    data = name_days(data)

    max_val = max(x for _, x in data)

    console.print("[magenta b u]F/R RATIO GRAPH FOR THE PAST 7 DAYS\n")
    console.print("[green on green]0[/][green b] Good (above 2)   ", end="")
    console.print("[red on red]0[/][red b] Bad (below 2)\n")

    for key, val in data:
        l = int(50 * val / max_val)

        if val <= 2:
            out = "[red]"
        else:
            out = "[green]"

        if l > 1:
            out += "▇" * l
        else:
            out += "▏"

        console.print(f"[blue]{key}[/] : {out} [/][b]{val:.2f}")

    print("")
    avg = mean([x for _, x in data])
    if avg >= 2:
        avg = f"[green b]{avg:.2f}"
    else:
        avg = f"[red b]{avg:.2f}"

    console.print(f"Average of past week: {avg}\n")


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
            stats.update_focus(t)
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
            stats.update_rest(t)
            quit()

        if not dur:
            dur = R_DEFAULT

        render_timer("rest", dur, flag)

    case "stats", _, flag:
        if flag in ["-h", "--help"]:
            help("stats")

        elif flag in ["-g", "--graph"]:
            render_graph()

        else:
            try:
                ratio = stats.total_time_focused / stats.total_time_rested
                if ratio > 2:
                    ratio = f"[green b]{ratio:.2f}"
                else:
                    ratio = f"[red b]{ratio:.2f}"
            except ZeroDivisionError:
                ratio = "[red b]No rest today"

            fm, fs = divmod(stats.total_time_focused, 60)
            fdat = f"[green b]{fm}[/] minutes"
            if fs:
                fdat += f" [green b]{fs}[/] seconds"

            rm, rs = divmod(stats.total_time_rested, 60)
            rdat = f"[magenta b]{rm}[/] minutes"
            if rs:
                rdat += f" [magenta b]{rs}[/] seconds"

            with open(f"{DIR}/templates/stats_template.txt") as f:
                template = f.read()

            template = template.replace("{focused}", fdat)
            template = template.replace("{rested}", rdat)
            template = template.replace("{fcount}", f"{stats.focus_sessions_completed}")
            template = template.replace("{rcount}", f"{stats.rest_sessions_completed}")
            template = template.replace("{ratio}", ratio)

            console.print("[red b u]TODAY'S STATS[/]\n")
            console.print(template)

    case _:
        console.print("Invalid syntax. Use [b]python3 pomo.py -h[/] for help")
