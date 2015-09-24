import sys
import subprocess
import os

MACHINES = ["bencher3", "bencher5"]
DIR = "current_results"
ZOOM = "0", "300"
PYTHON = sys.executable

os.environ["PYTHONPATH"] = os.path.join(os.getcwd(), "krun")

def mk_config_path(m):
    return os.path.join(DIR, m, "warmup.krun")

def run_cmd(args):
    print(args)
    subprocess.call(" ".join(args), shell=True)

for m in MACHINES:
    config_path = mk_config_path(m)

    # Single graph, all data
    args = [PYTHON, "mk_graphs.py", "export", config_path, m]
    run_cmd(args)

    # Single graph, zoomed in
    args.extend(ZOOM)
    run_cmd(args)

# 2x2 graph
args = [PYTHON, "mk_graphs2x2.py", "export"]
for m in MACHINES:
    args.append(mk_config_path(m))
    args.append(m)
run_cmd(args)

# 2x2 graph zoomed in
args.extend(ZOOM)
run_cmd(args)
