import yaml
import csv
import re
import xml.etree.ElementTree as ET

modsmap = {
    "LC": "ctrl+",
    "RC": "ctrl+",
    "rctrl": "ctrl+",
    "ralt": "ctrl+",
    "lctrl": "ctrl+",
    "lalt": "ctrl+",
    "LS": "shift+",
    "RS": "shift+",
    "rshift": "shift+",
    "lshift": "shift+"
}


def clear(mod):
    for (k, v) in modsmap.items():
        if k in mod:
            mod = mod.replace(k, v)
    return mod.lower().replace("(", "").replace(")", "").replace("tilde", "`").replace("caret", "^")


def get_reserved(origin):
    with open(origin, "r") as f:
        data = yaml.safe_load(f.read())

    reserved_map = {
    }
    for (k, v) in data["morph"].items():
        v.pop("hold", None)
        v.pop("hold.bind", None)
        v.pop("config", None)
        v.pop("pos", None)
        v.pop("key", None)
        for (mod, key) in v.items():
            if not "shift" in mod or not "ctrl" in mod or not "alt" in mod or not "gui" in mod: continue
            m = clear(key)
            if m in ["ctrl+s", "ctrl+x", "ctrl+f", "ctrl+c", "ctrl+a", "ctrl+z", "ctrl+v", "ctrl+y"]:
                pass
            else:
                reserved_map[m] = modsmap[mod] + k.lower()

    return reserved_map


reserved = [
    ("<win reserved action>", "meta+shift+c"),
    ("<win reserved action>", "meta+shift+p"),
    ("<win reserved action>", "meta+shift+w"),
    ("<win reserved action>", "meta+shift+s"),
    ("<win reserved action>", "meta+shift+m"),
    ("<win reserved action>", "meta+shift+r"),
    ("<win reserved action>", "meta+shift+t"),
    ("<win reserved action>", "meta+shift+v"),
    ("<win reserved action>", "meta+ctrl+v"),
    ("<win reserved action>", "meta+ctrl+l"),
    ("<win reserved action>", "meta+ctrl+t"),
    ("<win reserved action>", "meta+ctrl+e"),
    ("<win reserved action>", "meta+ctrl+m"),
    ("<win reserved action>", "meta+ctrl+d"),
    ("<win reserved action>", "meta+ctrl+s"),
    ("<win reserved action>", "meta+ctrl+f"),
    ("<win reserved action>", "meta+ctrl+o"),
    ("<win reserved action>", "meta+ctrl+p"),
    ("<win reserved action>", "meta+ctrl+n"),
    ("<win reserved action>", "meta+ctrl+c"),
    ("<win reserved action>", "meta+ctrl+q"),
    ("<win reserved action>", "meta+alt+f"),
    ("<win reserved action>", "meta+alt+g"),
    ("<win reserved action>", "meta+alt+c"),
    ("<win reserved action>", "meta+alt+r"),
    ("<win reserved action>", "meta+alt+t"),
    ("<win reserved action>", "meta+alt+b"),
    ("<win reserved action>", "meta+alt+m"),
    ("<win reserved action>", "meta+alt+d"),
    ("<win reserved action>", "meta+alt+y"),
    ("<win reserved action>", "meta+alt+w"),
    ("<win reserved action>", "meta+ctrl+shift+v"),
    ("<win reserved action>", "meta+ctrl+shift+b"),
    ("<win reserved action>", "meta+ctrl+shift+t"),
    ("<win reserved action>", "meta+ctrl+shift+r"),
    ("<win reserved action>", "meta+ctrl+alt+v"),
    ("<win reserved action>", "meta+alt+shift+ctrl+v"),
]

ascii = {
    'add': '+',
    'closebracket': ']',
    'openbracket': ']',
    'backslash': '\\',
    'backquote': '`',
    'slash': '/',
    'comma': ',',
    'multiply': '*',
    'divide': '/',
    'subtract': '-',
    'period': '.',
    'quote': '\'',
    'space': 'space',
    'equals': '=',
    'minus': '-',
    'control': 'ctrl',
    # 'meta': 'ctrl',
}


def split_camel_case(camel_case_str):
    # Use a regular expression to find matches where a lowercase letter is followed by an uppercase letter
    split_words = re.sub('([a-z])([A-Z])', r'\1 \2', camel_case_str)
    return split_words.replace(".", " ")


def trans(key):
    if str(key) in ascii:
        return ascii[str(key)]
    return key


# Prepare data for CSV
def parse_xml(file):
    # Parse the XML content
    root = None
    with open(file, "r") as f:
        root = ET.fromstring(f.read())

    result = {}

    for action in root.findall('action'):
        action_id = action.get('id')
        context, description = "Main", action_id

        if '.' in action_id:
            context, description = action_id.split('.', 1)

        context, description = split_camel_case(context), split_camel_case(description)
        if context and context.lower().startswith("Editor"):
            context = "Editor"
        keys = []
        for shortcut in action.findall('keyboard-shortcut'):
            f = shortcut.get('first-keystroke')
            s = shortcut.get('second-keystroke')

            first = f.lower().replace("_", "") if f else None
            second = s.lower().replace("_", "") if s else None

            first_keystroke = "+".join(map(trans, str(first).split(" ")))
            second_keystroke = "+".join(map(trans, str(second).split(" ")))
            if second:
                keys.append(f"{first_keystroke} {second_keystroke}")
            else:
                keys.append(first_keystroke)

        # for shortcut in action.findall('mouse-shortcut'):
        #     keystroke = "+".join(shortcut.get('keystroke').split(" "))
        #     keys.append(keystroke)

        if keys:
            keys_combined = " OR ".join(keys)
        else:
            keys_combined = ""

        result[(description, context)] = keys_combined
    return result


def replace_fun(val):
    reserved_map = get_reserved("C:\\dev\\zmk-config\\shortcuts\\mods.yaml")

    for (r, s) in reserved_map.items():
        if r == val:
            return val.replace(r, s)

    return val


def write(target, data):
    # Define CSV file header
    csv_header = ["Description", "Keys", "Context", "Category", "Conf.", "Actions"]

    reserved_map = get_reserved("C:\\dev\\zmk-config\\shortcuts\\mods.yaml")

    done = []
    with open(target, mode='w', newline='') as file:
        writer = csv.writer(file, quoting=csv.QUOTE_ALL)
        writer.writerow(csv_header)
        for desc, val in reserved:
            if val in reserved_map.values(): continue
            done.append(val)
            if "meta" in val: continue
            writer.writerow([desc, val, "RESERVED", "General", "0", ""])
        for key, val in data.items():
            val = replace_fun(val)
            description, context = key
            if not val or "++" in val or "+-" in val:
                continue
            if val in done: continue
            if "meta" in val: continue
            if "$" in description or "redo" in description.lower() or "undo" in description.lower(): continue

            done.append(val)

            writer.writerow([description, val, context, "General", "0", ""])

    print(f"CSV file '{target}' has been created.")


def run(origin, target):
    # default = parse("C:\\dev\\zmk\\shortcut\\$default.xml")
    keymap = parse_xml(origin)
    # print(set(list((map(lambda x: (x[0],x[1]), data)))))
    # print(set(list(itertools.chain.from_iterable((map(lambda x: re.split("\s*(OR|\\+|>)\s*", x[1]), data))))))
    write(target, keymap)


# base = "C:\\dev\\zmk-config"
# run(f"{base}\\shortcuts\\keymap.xml", f"{base}\\shortcuts\\keymap.csv")
