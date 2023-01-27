import argparse
import os
import pickle
import time
from collections import defaultdict
from datetime import date

from rich import print
from rich.progress import BarColumn, Progress, TextColumn, TimeRemainingColumn

BAR_WIDTH = 50
F_DEFAULT = 20
R_DEFAULT = 5
TODAY = str(date.today())

parser = argparse.ArgumentParser()
mode = parser.add_mutually_exclusive_group()
mode.add_argument("-f", "--focus", help="focus mode", action="store_true")
mode.add_argument("-r", "--rest", help="rest mode", action="store_true")
mode.add_argument("-s", "--stats", help="statistics", action="store_true")
mode.add_argument(
    "-ct", "--clear-today", help="clear today's stats", action="store_true"
)
parser.add_argument(
    "-d", metavar="", dest="duration", help="duration of session in minutes", type=int
)
args = parser.parse_args()


class DailyStat:
    def __init__(self):
        self.reset()

    def reset(self):
        self.total_time_focused = 0
        self.total_time_rested = 0
        self.focus_sessions_completed = 0
        self.rest_sessions_completed = 0


try:
    with open("/home/nandu/.pomo/stats.dat", "rb+") as f:
        stat = pickle.load(f)
except FileNotFoundError:
    os.system("mkdir ~/.pomo/")
    open("/home/nandu/.pomo/stats.dat", "w").close()
    stat = {}


def save_data(data):
    stat[TODAY] = data
    with open("/home/nandu/.pomo/stats.dat", "wb") as f:
        pickle.dump(stat, f)


t_stat = stat.get(TODAY, DailyStat())


if args.focus:
    duration = F_DEFAULT
    if args.duration:
        duration = args.duration

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(complete_style="green", style="bright_black", bar_width=BAR_WIDTH),
        TimeRemainingColumn(),
    ) as progress:

        timer = progress.add_task("[yellow] Focus", total=duration * 60)
        while not progress.finished:
            progress.update(timer, advance=1)
            time.sleep(1)
        else:
            t_stat.total_time_focused += duration
            t_stat.focus_sessions_completed += 1
            save_data(t_stat)

elif args.rest:
    duration = R_DEFAULT
    if args.duration:
        duration = args.duration

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(complete_style="magenta", style="bright_black", bar_width=BAR_WIDTH),
        TimeRemainingColumn(),
    ) as progress:

        timer = progress.add_task("[yellow] Break", total=duration * 60)
        while not progress.finished:
            progress.update(timer, advance=1)
            time.sleep(1)
        else:
            t_stat.total_time_rested += duration
            t_stat.rest_sessions_completed += 1
            save_data(t_stat)

elif args.stats:
    print(f"[yellow b u]TODAY'S STATS\n")
    print(f"Total time focused                 {t_stat.total_time_focused}")
    print(f"Total time rested                  {t_stat.total_time_rested}")
    print(f"Focus sessions completed           {t_stat.focus_sessions_completed}")
    print(f"Rest sessions completed            {t_stat.rest_sessions_completed}")

elif args.clear_today:
    confirm = input(
        "Are you sure you want to reset all of today's progress? [y/n] (n): "
    )
    if confirm.lower() == "y":
        t_stat.reset()
        save_data(t_stat)
        print("[green]Data was successfully reset")
    else:
        print("[red b]Cancelled.")

else:
    print("Use [green b]pomo -h[/] for help")
