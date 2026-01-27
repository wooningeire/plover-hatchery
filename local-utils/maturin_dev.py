import argparse
import os
from pathlib import Path

def _main(args: argparse.Namespace, rest: list[str]):
    os.chdir(args.plover_path)

    root_path = Path(__file__).parent.parent
    wheels_path = root_path / Path(r"./plover_hatchery_lib_rs/target/wheels/")

    # if os.path.isdir(wheels_path):
    #     os.unlink(wheels_path)

    exit_code = os.system(fr"plover_console -s plover_send_command quit")
    if exit_code != 0:
        raise Exception

    options = " ".join(
        f"\"{arg}\"" if " " in arg else arg
        for arg in rest
    )

    manifest_path = root_path / Path(r"./plover_hatchery_lib_rs/Cargo.toml")

    exit_code = os.system(fr"maturin build --manifest-path {manifest_path} {options}")
    if exit_code != 0:
        raise Exception

    for filename in os.listdir(wheels_path):
        exit_code = os.system(fr"""plover_console -s plover_plugins install "{wheels_path / filename}" --force-reinstall""")
        if exit_code != 0:
            raise Exception


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    _ = parser.add_argument("--plover-path", help="Path to the directory that directly contains Plover's python_console binary", default=r"C:/Program Files/Open Steno Project/Plover 5.1.0")
    args, rest = parser.parse_known_args()
    
    _main(args, rest)