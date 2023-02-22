import argparse
from collections import namedtuple

CliArgs = namedtuple("CliArgs", ["parse", "report", "force"])


def handle_cli_args() -> CliArgs:
    """ Handle CLI arguments """
    parser = argparse.ArgumentParser(description='Handle file operations')
    parser.add_argument('--parse', '-p', action='store_true', help='Flag to run the parser')
    parser.add_argument('--report', '-r', action='store_true', help='Flag to run the report')
    parser.add_argument('--force', '-f', action='store_true', help='Force run the stream scheduler')
    args = parser.parse_args()

    return CliArgs(**{k: v for k, v in args._get_kwargs()})
