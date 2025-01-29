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
    config = f"{base}/draw/config.yaml"
    keymap = f"{base}/config/glove80.keymap"
    parsed = f"{base}/draw/parsed.yml"

    combosfile = f"{base}/draw/combos.yml"
    reduced = f"{base}/draw/reduced.yml"
    out_combos = f"{base}/draw/keymap-combos.svg"
    out_reduced = f"{base}/draw/keymap-reduced.svg"
    out_origin = f"{base}/draw/keymap.svg"
    
    print("[drawer] Parsing")
    subprocess.call(f"keymap.exe -c {config} parse -z {keymap} -o {parsed}",
                    creationflags=subprocess.CREATE_NO_WINDOW)
    origin = load(parsed)
    layout = {"layout": {"qmk_keyboard": "glove80"}}

    combosd = origin["combos"]
    save(combosfile, layout| {"combos": combosd, "layers": {"main": ['']*80}})

    layers = origin["layers"]
    removelayers(layers)
    # save(reduced, layout | {"layers": layers, "combos": origin["combos"]})


    print("[drawer] Drawing")


    subprocess.call(f"keymap.exe -c {config} draw {parsed} -o {out_origin}",
                    creationflags=subprocess.CREATE_NO_WINDOW)
    subprocess.call(f"keymap.exe -c {config} draw {combosfile} -o {out_combos}",
                    creationflags=subprocess.CREATE_NO_WINDOW)
    subprocess.call(f"keymap.exe -c {config} draw {reduced} -o {out_reduced}",
                    creationflags=subprocess.CREATE_NO_WINDOW)
    print("[drawer] Done")

#run("C:\\dev\\zmk-config")