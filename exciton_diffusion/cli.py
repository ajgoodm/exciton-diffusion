import click


@click.group()
def cli():
    """Entrypoint for word-ladder cli."""


@cli.command()
def what_time_is_it():
    print("PARTY TIME!")
