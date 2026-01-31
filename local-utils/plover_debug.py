import argparse
import os
from pathlib import Path
import time

def _main(args: argparse.Namespace):
    os.chdir(args.plover_path)

    exit_code = os.system(fr"plover_console -s plover_send_command quit")
    if exit_code != 0:
        raise Exception
    
    time.sleep(2)

    if args.reinstall:
        exit_code = os.system(fr"""plover_console -s plover_plugins install -e {Path(__file__).parent.parent}""")
        if exit_code != 0:
            raise Exception

        time.sleep(30)

    exit_code = os.system(fr"""plover_console -l debug""")
    if exit_code != 0:
        raise Exception


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    _ = parser.add_argument("--plover-path", help="Path to the directory that directly contains Plover's python_console binary", default=r"C:/Program Files/Open Steno Project/Plover 5.1.0")
    _ = parser.add_argument("--reinstall", "-r", action="store_true", help="Reinstall the plugin")
    args = parser.parse_args()
    
    _main(args)