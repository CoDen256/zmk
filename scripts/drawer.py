import pathlib
import yaml
import subprocess
import keymap_drawer

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
def run(base):
    root = "/zmk"
    config = f"{root}/draw/config.yaml"
    keymap = f"{root}/config/glove80.keymap"
    parsed = f"{root}/draw/parsed.yml"

    combosfile = f"{root}/draw/combos.yml"
    out_combos = f"{root}/draw/keymap-combos.svg"
    out_origin = f"{root}/draw/keymap.svg"

    cmd = f"{base}/scripts/keymap_drawer"
    args = {}#{"creationflags": subprocess.CREATE_NO_WINDOW}

    print("[drawer] Parsing")
    subprocess.call(f"{cmd} -c {config} parse -z {keymap} -o {parsed}", **args)

    origin = load(parsed)
    layout = {"layout": {"qmk_keyboard": "glove80"}}

    combosd = origin["combos"]
    save(combosfile, layout| {"combos": combosd, "layers": {"main": ['']*80,"main_upper": ['']*80}})

    layers = origin["layers"]
    removelayers(layers)
    # save(reduced, layout | {"layers": layers, "combos": origin["combos"]})


    print("[drawer] Drawing")


    subprocess.call(f"{cmd} -c {config} draw {parsed} -o {out_origin}", **args)
    subprocess.call(f"{cmd} -c {config} draw {combosfile} -o {out_combos}", **args)
    print("[drawer] Done")

if __name__ == '__main__':
    run(pathlib.Path(__file__).parent.parent.resolve())