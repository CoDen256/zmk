import yaml

keynames = {
    "!": "EXCLAMATION",
    "@": "AT_SIGN",
    "#": "HASH",
    "$": "DOLLAR",
    "%": "PERCENT",
    "^": "CARET",
    "&": "AMPERSAND",
    "*": "ASTERISK",
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
    "\"": "DOUBLE_QUOTES",
    ",": "COMMA",
    "<": "LESS_THAN",
    ".": "PERIOD",
    ">": "GREATER_THAN",
    "[": "LEFT_BRACKET",
    "{": "LEFT_BRACE",
    "]": "RIGHT_BRACKET",
    "}": "RIGHT_BRACE",
    "`": "GRAVE",
    " ": "SPACE",
    "~": "TILDE",
    "0": "NO",
    "1": "N1",
    "2": "N2",
    "3": "N3",
    "4": "N4",
    "5": "N5",
    "6": "N6",
    "7": "N7",
    "8": "N8",
    "9": "N9",
    "n0": "KP_NO",
    "n1": "KP_N1",
    "n2": "KP_N2",
    "n3": "KP_N3",
    "n4": "KP_N4",
    "n5": "KP_N5",
    "n6": "KP_N6",
    "n7": "KP_N7",
    "n8": "KP_N8",
    "n9": "KP_N9",
}


def kp(key):
    if key in keynames:
        return f"&kp {keynames[key]}"
    return f"&kp {key}"


class Macro():

    def __init__(self, seq, name=None):
        self.seq = seq.removeprefix("^")
        self._name = name

    def __str__(self):
        return f"{self.seq}"

    def __repr__(self):
        return f"{self.seq}"

    def sequence_binding(self):
        return [kp(k) for k in self.seq]

    def name(self):
        if self._name: return self._name
        return ("_".join([k[4:].lower() for k in self.sequence_binding()]))

    def node(self):
        return "&"+ self.name()
    def compile(self):
        seq = " ".join(self.sequence_binding())
        return f'''
{self.name()}: {self.name()} {{
compatible = "zmk,behavior-macro";
label = "{self.name().upper()}";
#binding-cells = <0>;
tap-ms = <0>;
wait-ms = <0>;
bindings = <&macro_tap>,<{seq}>;
}};
'''


class Binder():

    def __init__(self, macros):
        self._macros = {m.seq: m for m in macros}

    def macros(self):
        return self._macros.values()

    def get_macros(self, seq):
        if seq in self._macros:
            return self._macros[seq].node()
        macro = Macro(seq)
        self._macros[seq] = macro
        return macro.node()

    def binding(self, key):
        if not key: return "&none"
        if len(key) == 1: return kp(key)
        if key[0] == "&" and key[1].isalpha():
            return key
        if key[0] == "^" and key[1].isalnum():
            return self.get_macros(key[1:])
        if key[0].isalnum():
            return kp(key)
        # must be macros
        return self.get_macros(key)


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
    def __init__(self, layout, binder, pos, out, cfg):
        self.layout = layout
        self.out = out
        self.binder = binder
        self.key_names = pos
        self.pos = " ".join([str(layout.pos(k)) for k in list(pos)])
        self.cfg = cfg

    def compile(self):
        return f'''{self.key_names} {{
bindings = <{self.binder.binding(self.out)}>; 
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
            self.pos = layout.opposite_side(tap.default) if not position else list(
                map(lambda k: layout.pos(k), position.split(" ")))

    def compile(self):
        root, generated = self.tap.compile()
        label = self.tap.label + "_key" if len(self.tap.label) == 1 else self.tap.label
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
    def __init__(self, binder, label, default, mapping):
        self.label = label
        self.default = default
        self.mapping = mapping
        self.binder = binder

    def generate(self):
        sinks = []
        links = []
        prev = self.binder.binding(self.default)
        for (key, value) in self.mapping.items():
            mods_complement = set(modmap.keys()) - {key}
            sink = Morph(self.label, "sink",
                         self.binder.binding(value), mods_complement,
                         self.binder.binding(self.default), True, key)
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
    configdata = data['config']
    def_config = Config(**configdata)
    pos = Positioning(**data['keys'])

    macros = []
    for (name, seq) in data['macros'].items():
        macros.append(Macro(seq, name))

    binder = Binder(macros)

    maps = []
    for (label, mapping) in data['map'].items():
        cfg = def_config
        hold = None
        if "hold" in mapping:
            hold_cfg = mapping.pop("hold")
            hold = hold_cfg.pop("bind")
            cfg = Config(**(configdata | hold_cfg))
        if "hold.bind" in mapping:
            hold = mapping.pop("hold.bind")

        map = Map(binder, label, mapping.pop("key", label), mapping)
        maps.append(HoldTap(pos, cfg, map, hold, mapping.pop("pos", None)))

    combos = []
    combodef = data['combos']
    default = combodef.pop("timeout")
    for (src, out) in combodef.items():
        timeout = default
        if "  " in out:
            out, timeout = out.split("  ")
        combos.append(Combo(pos, binder, src, out, ComboCfg(int(timeout))))
    return maps, combos, binder


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


def run0(origin, target):
    print(f"[modder] Reading {origin}")
    mappings, combos, binder = parse(origin)
    hardcoded_macros = len(binder.macros())
    print(f"[modder] Parsed {len(mappings)} mappings")
    print(f"[modder] Parsed {len(combos)} combos")

    content = ""
    for m in mappings:
        content += m.compile() + "\n"

    combocontent = ""
    for c in combos:
        combocontent += c.compile() + "\n"

    macros = binder.macros()  # stateful
    print(macros)
    print(f"[modder] Parsed {hardcoded_macros} + generated {len(macros) - hardcoded_macros} macros")
    macroscontent = "\n".join([m.compile() for m in macros])
    update(target, content, "/*<mods-start>*/", "/*<mods-end>*/")
    update(target, combocontent, "/*<combos-start>*/", "/*<combos-end>*/")
    update(target, macroscontent, "/*<macros-start>*/", "/*<macros-end>*/")


def run(origin, target):
    return run0(origin, target)
# run("C:\\dev\\zmk-config\\shortcuts\\mods.yaml", "C:\\dev\\zmk-config\\config\\glove80.keymap")


#
# a = parse("C:\\dev\\zmk-config\\shortcuts\\mods.yaml")
# for i in a: print(i.compile())
