import os
import pickle
from datetime import date


class StatManager:
    DATAPATH = "/home/nandu/.pomo/stats.dat"
    DATE = str(date.today())

    def __init__(self):
        self.stats = self.get_stats()

    class DailyStat:
        def __init__(self):
            self.total_time_focused = 0
            self.total_time_rested = 0
            self.focus_sessions_completed = 0
            self.rest_sessions_completed = 0

    @property
    def total_time_focused(self):
        return self.get_todays_stats().total_time_focused

    @property
    def total_time_rested(self):
        return self.get_todays_stats().total_time_rested

    @property
    def focus_sessions_completed(self):
        return self.get_todays_stats().focus_sessions_completed

    @property
    def rest_sessions_completed(self):
        return self.get_todays_stats().rest_sessions_completed

    def get_todays_stats(self) -> DailyStat:
        return self.stats.get(self.DATE, self.DailyStat())

    def update_focus(self, dur: int):
        t = self.get_todays_stats()

        t.total_time_focused += dur
        t.focus_sessions_completed += 1

        self._save_stats(t)

    def update_rest(self, dur: int):
        t = self.get_todays_stats()

        t.total_time_rested += dur
        t.rest_sessions_completed += 1

        self._save_stats(t)

    def get_stats(self) -> dict:
        try:
            with open(self.DATAPATH, "rb+") as f:
                stats = pickle.load(f)
        except EOFError:
            stats = {}
        except FileNotFoundError:
            os.system(f"mkdir ~/.pomo/")
            open(self.DATAPATH, "w").close()
            stats = {}

        return stats

    def _save_stats(self, stat: DailyStat):
        self.stats[self.DATE] = stat
        with open(self.DATAPATH, "wb") as f:
            pickle.dump(self.stats, f)

    def get_past_data(self) -> list[tuple]:
        with open(self.DATAPATH, "rb") as f:
            stats = pickle.load(f)
        return sorted(stats.items(), key=lambda x: x[0])[-7:]


DailyStat = StatManager.DailyStat
__all__ = ["StatManager", "DailyStat"]
