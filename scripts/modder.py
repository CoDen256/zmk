import yaml
from pydantic import PositiveFloat

keynames = {
 "!": "EXCLAMATION",
 "@": "AT_SIGN",
 "#": "HASH",
 "$": "DOLLAR",
 "%": "PERCENT",
 "^": "CARET",
 "&": "AMPERSAND",
 "*/": "ASTERISK",
 "(": "LEFT_PARENTHESIS",
 ")": "RIGHT_PARENTHESIS",
 "=": "EQUAL",
 "+": "PLUS",
 "-": "MINUS",
 "_": "UNDERSCORE",
 "/": "SLASH",
 "?": "QUESTION",
 "\\": "BACKSLASH",
 "|": "PIPE",
 ";": "SEMICOLON",
 ":": "COLON",
 "'": "SINGLE_QUOTE",
 "": "DOUBLE_QUOTES",
 ",": "COMMA",
 "<": "LESS_THAN",
 ".": "PERIOD",
 ">": "GREATER_THAN",
 "[": "LEFT_BRACKET",
 "{": "LEFT_BRACE",
 "]": "RIGHT_BRACKET",
 "}": "RIGHT_BRACE",
 "`": "GRAVE",
 "~": "TILDE",
}

def kp(key):
    if key in keynames:
        key = keynames[key]
    return f"&kp {key}"

modmap = {
    "lalt": "MOD_LALT",
    "ralt": "MOD_RALT",
    "lctrl": "MOD_LCTL",
    "rctrl": "MOD_RCTL",
    "lgui": "MOD_LGUI",
    "rgui": "MOD_RGUI",
    "lshift": "MOD_LSFT",
    "rshift": "MOD_RSFT",
}

positions = {
    "left": "28 29 30 31 32 40 41 42 43 44 58 59 60 61 62 75 76 77 78 79 69 70 71 72 73 74",
    "right": "27 26 25 24 23 39 38 37 36 35 51 50 49 48 47 68 67 66 65 64 15 14 13 12 11 10 69 70 71 72 73 74"
}

keys_pos = {
    "left": "kghcwoainjfupq",
    "right": "vlbtresmdyxz"
}

key_to_pos = {}
for (pos, keys) in keys_pos.items():
    for k in keys:
        key_to_pos[k.upper()] = positions[pos]


class Positioning():
    def __init__(self, left, right):
        self.left = left
        self.right = right
        self.keys = left | right

    def lefts(self):
        return self.left.values()

    def rights(self):
        return self.right.values()

    def get_side(self, key):
        if key.isnumeric():
            return "left" if key in self.lefts() else "right"
        return "left" if key in self.left.keys() else "right"

    def pos(self, key):
        return self.keys[key]

    def opposite_side(self, key):
        return self.rights() if self.get_side(key) == "left" else self.lefts()

    def same_side(self, key):
        return self.lefts() if self.get_side(key) == "left" else self.rights()

class ComboCfg:
    def __init__(self, timeout):
        self.timeout = timeout

class Combo:
    def __init__(self, layout, pos, out, cfg):
        self.layout = layout
        self.out = out if "&" in out and len(out) != 1 else kp(out)
        self.key_names = pos
        self.pos = " ".join([str(layout.pos(k)) for k in list(pos)])
        self.cfg = cfg

    def compile(self):
        return f'''{self.key_names} {{
bindings = <{self.out}>; 
timeout-ms = <{self.cfg.timeout}>;
key-positions = <{self.pos}>;}};
'''


class Config:
    def __init__(self, tapping_term, quick_tap, prior_idle):
        self.tapping_term = tapping_term
        self.quick_tap = quick_tap
        self.prior_idle = prior_idle


class HoldTap:
    def __init__(self, layout, config, tap, hold, position):
        self.tap = tap
        self.hold = hold
        self.config = config
        self.layout = layout
        if hold:
            self.pos = layout.opposite_side(tap.default) if not position else list(map(lambda k: layout.pos(k), position.split(" ")))

    def compile(self):
        root, generated = self.tap.compile()
        label = self.tap.label + "_key"
        if not self.hold:
            return generated.replace(root[1:], label).replace(root[1:].upper(), label.upper())
        return self.gen_holdtap(label, self.hold, root, self.pos) + "\n" + generated

    def gen_holdtap(self, name, hold, tap, position):
        join = ' '.join(map(lambda x: str(x), position))
        return f'''
{name}:{name} {{
compatible = "zmk,behavior-hold-tap";
#binding-cells = <2>;
flavor = "balanced";
tapping-term-ms = <{self.config.tapping_term}>;
quick-tap-ms = <{self.config.quick_tap}>;
require-prior-idle-ms = <{self.config.prior_idle}>;
bindings = <{hold}>, <{tap}>;
hold-trigger-key-positions = <{join}>;
hold-trigger-on-release;
label = "{name.upper()}";}};
'''


class Morph:
    def __init__(self, label, prefix, default, mods, modified, keep=False, postfix=""):
        self.label = label
        self.prefix = prefix
        self.postfix = postfix if postfix else f"{'_'.join(mods)}"
        self.default = default
        self.mods = mods
        self.modified = modified
        self.keep = keep

    def name(self):
        return f"{self.label}_{self.prefix}_{self.postfix}"

    def compile(self):
        label = self.name()
        m = sorted(list(map(lambda x: modmap[x], self.mods)))
        joined = "|".join(m)
        mods = f"<({joined})>"
        keep_mods = f"keep-mods = {mods};" if self.keep else ""
        return f"""
{label}:{label}{{
compatible = "zmk,behavior-mod-morph";
#binding-cells = <0>;
bindings = <{self.default}>, <{self.modified}>;
label = "{label.upper()}";
mods = {mods};
{keep_mods}
}};"""


class Map:
    def __init__(self, label, default, mapping):
        self.label = label
        self.default = default
        self.mapping = mapping

    def generate(self):
        sinks = []
        links = []
        prev = kp(self.default) if "&" not in self.default else self.default
        for (key, value) in self.mapping.items():
            mods_complement = set(modmap.keys()) - {key}
            sink = Morph(self.label, "sink",
                         kp(value), mods_complement,
                         kp(self.default), True, key)
            sinks.append(sink)
            link = Morph(self.label, "link",
                         prev, [key],
                         self.gen_ref(sink))
            links.append(link)
            prev = self.gen_ref(link)

        return prev, links + sinks

    def gen_ref(self, morph):
        return f"&{morph.name()}"

    def compile(self):
        c = ""
        prev, r = self.generate()
        for i in r:
            c += i.compile() + "\n"
        return prev, c


# Function to parse the YAML content and create the list of Map objects
def parse(file):
    # Parse the YAML content
    with open(file, "r") as f:
        data = yaml.safe_load(f.read())

    # Create the list of Map objects
    mapdata = data['map']
    combodata = data['combos']
    configdata = data['config']
    def_config = Config(**configdata)
    pos = Positioning(**data['keys'])
    maps = []
    for (label, mapping) in mapdata.items():
        cfg = def_config
        hold = None
        if "hold" in mapping:
            hold_cfg = mapping.pop("hold")
            hold = hold_cfg.pop("bind")
            cfg = Config(**(configdata | hold_cfg))
        if "hold.bind" in mapping:
            hold = mapping.pop("hold.bind")

        map = Map(label, mapping.pop("key", label), mapping)
        maps.append(HoldTap(pos, cfg, map, hold, mapping.pop("pos", None)))

    combos = []
    default = combodata.pop("timeout")
    for (src, out) in combodata.items():
        timeout = default
        if " " in out:
            out, timeout = out.split(" ")
        combos.append(Combo(pos, src, out, ComboCfg(int(timeout))))

    return maps, combos


def update(target, content, start_line, end_line):
    print(f"[modder] Start writing to {target}")
    start = start_line
    end = end_line
    new = []
    target_region = False
    with open(target, "r") as f:
        for line in f.readlines():
            if end in line and target_region:
                for l in content.split("\n"):
                    new.append(l + "\n")
                target_region = False
                new.append(end + "\n")
                continue
            if target_region:
                continue
            if start in line and not target_region:
                target_region = True
                new.append(start + "\n")
                continue
            new.append(line)
    with open(target, "w") as f:
        f.writelines(new)
    print(f"[modder] Done writing to {target}")


def run(origin, target):
    print(f"[modder] Reading {origin}")
    mappings, combos = parse(origin)
    print(f"[modder] Parsed {len(mappings)} mappings")
    content = ""
    for m in mappings:
        content += m.compile() + "\n"
    combocontent = ""
    for c in combos:
        combocontent += c.compile() + "\n"
    update(target, content, "/*<mods-start>*/", "/*<mods-end>*/")
    update(target, combocontent, "/*<combos-start>*/", "/*<combos-end>*/")

# run("C:\\dev\\zmk-config\\shortcuts\\mods.yaml", "C:\\dev\\zmk-config\\config\\glove80.keymap")


#
# a = parse("C:\\dev\\zmk-config\\shortcuts\\mods.yaml")
# for i in a: print(i.compile())
