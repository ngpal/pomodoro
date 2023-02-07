import click

from src.rendermanager import RenderManager
from src.statmanager import DailyStat, StatManager

stat = StatManager()
rm = RenderManager()


@click.group
def cli():
    """Become more productive right from the terminal!"""


@cli.command
@click.argument("dur", default=0)
@click.option("-f", "mode", flag_value="focus", help="Enter focus mode", default=True)
@click.option("-r", "mode", flag_value="rest", help="Enter rest mode")
@click.option("-q", "quiet", is_flag=True, help="Does not ding at the end")
def timer(dur, mode, quiet):
    """Enters timer mode (default focus 10 mins)"""
    t = rm.render_timer(mode, dur, quiet)
    stat.update(mode, t)


@cli.command
@click.option("-f", "mode", flag_value="focus", help="Enter focus mode", default=True)
@click.option("-r", "mode", flag_value="rest", help="Enter rest mode")
def stopwatch(mode):
    """Enter stopwatch mode (default focus)"""
    t = rm.render_stopwatch(mode)
    stat.update(mode, t)


@cli.command
@click.option("-g", "graph", is_flag=True, help="Shows f/r graph for the last week")
def stats(graph):
    """See stats"""
    if graph:
        rm.render_graph()
    else:
        rm.render_stats()


__all__ = ["cli", "DailyStat"]
