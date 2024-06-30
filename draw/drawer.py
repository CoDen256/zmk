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
    out_parsed = "./draw/keymap-parsed.svg"
    
    print("Parsing")
    subprocess.call(f"keymap.exe -c {config} parse -z {keymap} -o {parsed}")


    origin = load_parsed(parsed)
    remove_keys(origin)
    save_parsed(updated, origin)
    print("Drawing")

    # subprocess.call(f"keymap.exe -c {config} draw {parsed} -o {out_parsed}")
    subprocess.call(f"keymap.exe -c {config} draw {updated} -o {out}")
