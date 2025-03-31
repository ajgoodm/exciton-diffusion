from pathlib import Path

import click

from analysis.cli.utils import data_directory
from analysis.show.excitations import plot


@click.group
def show() -> None:
    ...


@show.command
@data_directory
def excitation_data(data_directory: Path) -> None:
    plot(data_directory)
