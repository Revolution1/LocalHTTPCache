import logging

import click
import hosts

log = logging.getLogger('lhc')


@click.group()
def main():
    """
    LHC (Local HTTP Cache), cache static files to your local machine
    """


@main.command()
def install():
    """
    install guide to setup LHC
    """


@main.command()
def status():
    """
    show the running status of LHC
    """
    click.echo('Initialized the database')


@main.command()
def run():
    """
    run LHC proxy
    """
    click.echo('Initialized the database')


@main.command()
def stop():
    """
    stop LHC proxy
    """
    click.echo('Initialized the database')


@main.command()
def destroy():
    """
    stop LHC proxy and clean all the configures
    """
    click.echo('Initialized the database')


@main.command()
def ls():
    """
    list hosts
    """
    click.echo('Initialized the database')


@main.command()
def add():
    """
    add a host
    """
    click.echo('Initialized the database')


@main.command('del')
def delete():
    """
    delete a host
    """
    click.echo('Initialized the database')


if __name__ == '__main__':
    main()
