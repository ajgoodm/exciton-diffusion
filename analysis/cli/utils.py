from pathlib import Path

import click


def str_to_path(_, __, value: str) -> Path:  # type: ignore[no-untyped-def]
    return Path(value)


data_directory = click.option(
    "--data-directory",
    type=click.Path(exists=True, file_okay=False),
    callback=str_to_path,
    required=True,
)
