import pathlib
import yaml
import subprocess
import sys

layers = ["main"]
def load(file):
    with open(file, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def save(file, out):
    with open(file, 'w',  encoding='utf-8') as yaml_file:
        yaml.dump(out, yaml_file, default_flow_style=False, sort_keys=False)

def removelayers(origin):
    for layer in list(origin.keys()):
        if layer not in layers:
            del origin[layer]
def run(base, cmd='keymap'):
    root = base

    config = f"{root}/draw/config.yaml"
    keymap = f"{root}/config/glove80.keymap"

    out_combos_parsed = f"{root}/draw/combos.yml"
    out_parsed = f"{root}/draw/parsed.yml"
    out_reduced = f"{root}/draw/reduced.yml"

    compiled_combos = f"{root}/draw/keymap-combos.svg"
    compiled_origin = f"{root}/draw/keymap.svg"
    compiled_reduced = f"{root}/draw/keymap.svg"

    args = {}

    print("[drawer] Parsing")
    print(subprocess.run([cmd, '-c', config, "parse", "-z", keymap, "-o", out_parsed]))

    origin = load(out_parsed)
    layout = {"layout": {"qmk_keyboard": "glove80"}}

    combos = origin["combos"]
    save(out_combos_parsed, layout| {"combos": combos, "layers": {"main": ['']*80}})

    layers = origin["layers"]
    removelayers(layers)
    save(out_reduced, layout | {"layers": layers, "combos": origin["combos"]})


    print("[drawer] Drawing")

    print(subprocess.run([cmd, '-c', config, "draw", out_parsed, "-o", compiled_origin]))
    #print(subprocess.run([cmd, '-c', config, "draw", out_combos_parsed, "-o", compiled_combos]))
    #print(subprocess.run([cmd, '-c', config, "draw", out_reduced, "-o", compiled_reduced]))
    print("[drawer] Done")

if __name__ == '__main__':
    keymap_bin = "keymap"
    if (len(sys.argv) >= 1):
        keymap_bin = sys.argv[1]

    print(f"Running python with keymap: {keymap_bin}")
    print(subprocess.run([keymap_bin, '-v']))
    run(pathlib.Path(__file__).parent.parent.resolve(), keymap_bin)