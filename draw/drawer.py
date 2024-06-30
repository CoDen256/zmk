import yaml
import sys
import subprocess

def load_parsed(file):
    with open(file, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def save_parsed(file, out):
    with open(file, 'w',  encoding='utf-8') as yaml_file:
        yaml.dump(out, yaml_file, default_flow_style=False, sort_keys=False)

def remove_keys(origin):
    for keys in origin["layers"].values():
        for key in range(len(keys)):
            keys[key] = ''

if __name__ == '__main__':
    config = "./draw/config.yaml"
    keymap = "./config/glove80.keymap"
    parsed = "./draw/parsed.yml"

    updated = "./draw/updated.yml"
    out = "./draw/keymap.svg"
    
    subprocess.call(f"keymap.exe -c {config} parse -z {keymap} -o {parsed}")

    combos_only = False
    if len(sys.argv) > 1 and sys.argv[1] == 'c':
        combos_only = True

    origin = load_parsed(parsed)
    if combos_only:
        remove_keys(origin)
    save_parsed(updated, origin)

    subprocess.call(f"keymap.exe -c {config} draw {updated} -o {out}")
