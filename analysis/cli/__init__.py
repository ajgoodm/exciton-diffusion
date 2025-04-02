import click

from analysis.cli.show import show


@click.group
def analyze() -> None:
    ...


analyze.add_command(show)
