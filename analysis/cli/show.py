from pathlib import Path

import click

from analysis.cli.utils import data_directory
from analysis.show.excitations import plot as plot_excitations
from analysis.show.simulation_output import plot as plot_simulation_output


@click.group
def show() -> None:
    ...


@show.command
@data_directory
def excitation_data(data_directory: Path) -> None:
    plot_excitations(data_directory)


@show.command
@data_directory
def simulation_output(data_directory: Path) -> None:
    plot_simulation_output(data_directory)
