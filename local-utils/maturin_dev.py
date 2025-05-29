import argparse
import os
from pathlib import Path

def _main(args: argparse.Namespace):
    wheels_path = Path(r"./plover_hatchery_lib_rs/target/wheels/")

    
    # os.unlink(wheels_path)

    exit_code = os.system(fr"maturin build --manifest-path ./plover_hatchery_lib_rs/Cargo.toml {args.options}")
    if exit_code != 0:
        raise Exception

    for filename in os.listdir(wheels_path):
        exit_code = os.system(fr"""plover_console -s plover_plugins install "{wheels_path / filename}" --force-reinstall""")
        if exit_code != 0:
            raise Exception


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--options", help="options to pass to `maturin build`", default="")
    args = parser.parse_args()
    
    _main(args)