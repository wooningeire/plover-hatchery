import argparse
import os
from pathlib import Path

def _main(args: argparse.Namespace):
    os.chdir(args.plover_path)

    exit_code = os.system(fr"plover_console -s plover_send_command quit")
    if exit_code != 0:
        raise Exception
    
    plugin_path = Path(__file__).parent.parent

    exit_code = os.system(fr"""plover_console -s plover_plugins install -e {plugin_path}""")
    if exit_code != 0:
        raise Exception


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    _ = parser.add_argument("--plover-path", help="Path to the directory that directly contains Plover's python_console binary", default=r"C:/Program Files/Open Steno Project/Plover 5.0.0.dev1")
    args = parser.parse_args()
    
    _main(args)