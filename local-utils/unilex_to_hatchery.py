from pathlib import Path
import os
import timeit
import argparse
    
from plover import system
from plover.config import DEFAULT_SYSTEM_NAME
from plover.registry import registry





def _setup_plover():
    registry.update()
    system.setup(DEFAULT_SYSTEM_NAME)



def _main(args: argparse.Namespace):
    from plover_hatchery.lib.dictionary_generation import generate

    root = Path(os.getcwd())

    in_path = root / args.in_unilex_path
    
    out_path = root / args.out_path
    out_path.parent.mkdir(exist_ok=True, parents=True)
    
    if args.failures_out_path is not None:
        failures_out_path = root / args.failures_out_path
        failures_out_path.parent.mkdir(exist_ok=True, parents=True)
    else:
        failures_out_path = None


    print(f"Generating entries…")
    duration = timeit.timeit(lambda: generate(in_path, out_path, failures_out_path), number=1)
    print(f"Finished (took {duration} s)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # parser.add_argument("-j", "--in-json-path", "--in-json", help="path to the input JSON dictionary", required=True)  
    parser.add_argument("-u", "--in-unilex-path", "--in-unilex", help="path to the input Unilex lexicon", required=True)
    parser.add_argument("-o", "--out-path", "--out", help="path to output the Hatchery dictionary (to use in Plover, use the `hatchery` file extension)", required=True)
    parser.add_argument("-f", "--failures-out-path", "--failout", help="path to output the failed entries")
    args = parser.parse_args()

    _setup_plover()  
    _main(args)