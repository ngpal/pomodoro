import re

from src.rendermanager import RenderManager
from src.statmanager import DailyStat, StatManager


class CommandManager:
    F_DEFAULT = 20
    R_DEFAULT = 5
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

    def parse_args(self, args: str) -> list:
        args_list = args.split()
        if self.ARG_PATTERS["cmd"].match(args):
            return [args_list[0], None, None]
        elif self.ARG_PATTERS["cmd dur"].match(args):
            return [args_list[0], int(args_list[1]), None]
        elif self.ARG_PATTERS["cmd flag"].match(args):
            return [args_list[0], None, args_list[1]]
        elif self.ARG_PATTERS["stats flag"].match(args):
            return ["stats", None, args_list[1]]
        elif self.ARG_PATTERS["cmd dur flag"].match(args):
            return [args_list[0], int(args_list[1]), args_list[2]]
        return [None, None, None]

    def execute_cmd(self, args: list[str]):
        if not args or args[0] in ["-h", "--help"]:
            self.rm.render_help()
            quit()

        match self.parse_args(" ".join(args)):
            case cmd, _, flag if flag in ["-h", "--help"]:
                self.rm.render_help(cmd)

            case "focus", dur, flag:
                if flag in ["-s", "--stopwatch"]:
                    t = self.rm.render_stopwatch("[yellow]Focus[/]")
                else:
                    t = self.rm.render_timer("focus", dur or self.F_DEFAULT, flag)

                self.stats.update_focus(t)

            case "rest", dur, flag:
                if flag in ["-s", "--stopwatch"]:
                    t = self.rm.render_stopwatch("[yellow]Rest[/]")
                else:
                    t = self.rm.render_timer("rest", dur or self.R_DEFAULT, flag)

                self.stats.update_rest(t)

            case "stats", _, flag:
                if flag in ["-g", "--graph"]:
                    self.rm.render_graph()
                else:
                    self.rm.render_stats()

            case _:
                self.rm.console.print(
                    "Invalid syntax. Use [b]python3 pomo.py -h[/] for help"
                )


__all__ = ["CommandManager"]
