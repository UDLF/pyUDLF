"""
The API of previous pyUDLF versions (InputType + run_calls), which is still
supported and gives the same results as pyUDLF.UDLF.

    python examples/legacy_api.py

Uses the synthetic dataset of the repository (200 elements, 10 classes).
The output files are written to a temporary directory.
"""

import tempfile
from pathlib import Path

from pyUDLF import run_calls
from pyUDLF.utils.inputType import InputType

DATA = Path(__file__).resolve().parent.parent / "tests" / "data" / "synthetic"

with tempfile.TemporaryDirectory() as out:
    inp = InputType()                       # starts from the UDLF reference configuration
    inp.set_task("UDL")
    inp.set_method_name("CPRR")
    inp.set_input_file_format("RK")
    inp.set_rk_format("NUM")
    inp.set_input_file(str(DATA / "rk_num.txt"))
    inp.set_lists_file(str(DATA / "lists.txt"))
    inp.set_classes_file(str(DATA / "classes.txt"))
    inp.set_dataset_size(200)
    inp.set_method_parameters("CPRR", l=100, k=10)
    inp.set_effectiveness_precisions_to_compute([5, 10, 20])
    inp.set_effectiveness_recalls_to_compute([10])
    inp.set_output_file(True)
    inp.set_output_file_format("RK")        # the reference configuration writes a matrix
    inp.set_output_rk_format("NUM")
    inp.set_output_file_path(f"{out}/output")   # writes output.txt
    inp.set_output_log_file_path(f"{out}/log.txt")

    output = run_calls.run(inp, get_output=True, compute_individual_gain=True)

    output.print_log()                      # Before / After / Gain of each measure
    rks = output.get_rks(top_k=10)          # re-ranked lists (lists of ints)
    print(f"\nFirst re-ranked list (top 10): {rks[0]}")
    best = output.get_individual_gain_list(sort=True)[:3]
    print("Queries with the largest gain (gain, query):", best)
