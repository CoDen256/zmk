import yaml
import subprocess
import keymap_drawer

def load(file):
    with open(file, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def save(file, out):
    with open(file, 'w',  encoding='utf-8') as yaml_file:
        yaml.dump(out, yaml_file, default_flow_style=False, sort_keys=False)

def remove_keys(origin):
    for keys in origin["layers"].values():
        for key in range(len(keys)):
            keys[key] = ''

def run(base):
    config = f"{base}/draw/config.yaml"
    keymap = f"{base}/config/glove80.keymap"
    parsed = f"{base}/draw/parsed.yml"

    reduced = f"{base}/draw/reduced.yml"
    out_reduced = f"{base}/draw/keymap-reduced.svg"
    out_origin = f"{base}/draw/keymap.svg"
    
    print("[drawer] Parsing")
    subprocess.call(f"keymap.exe -c {config} parse -z {keymap} -o {parsed}")


    origin = load(parsed)
    remove_keys(origin)
    save(reduced, origin)
    print("[drawer] Drawing")

    subprocess.call(f"keymap.exe -c {config} draw {parsed} -o {out_origin}")
    subprocess.call(f"keymap.exe -c {config} draw {reduced} -o {out_reduced}")
    print("[drawer] Done")
