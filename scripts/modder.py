from cProfile import label

import yaml


modmap = {
    "lalt" : "MOD_LALT",
    "ralt" : "MOD_RALT",
    "lctrl" : "MOD_LCTL",
    "rctrl" : "MOD_RCTL",
    "lgui" : "MOD_LGUI",
    "rgui" : "MOD_RGUI",
    "lshift" : "MOD_LSFT",
    "rshift" : "MOD_RSFT",
}

positions = {
    "left" : "28 29 30 31 32 40 41 42 43 44 58 59 60 61 62 75 76 77 78 79 69 70 71 72 73 74",
    "right" : "27 26 25 24 23 39 38 37 36 35 51 50 49 48 47 68 67 66 65 64 15 14 13 12 11 10 69 70 71 72 73 74"
}


keys_pos = {
    "left" : "kghcwoainjfupq",
    "right" : "vlbtresmdyxz"
}

key_to_pos = {}
for (pos, keys) in keys_pos.items():
    for k in keys:
        key_to_pos[k.upper()] = positions[pos]

class Config:
    def __init__(self, tapping_term, quick_tap, prior_idle):
        self.tapping_term = tapping_term
        self.quick_tap = quick_tap
        self.prior_idle = prior_idle

class HoldTap:
    def __init__(self, config, tap, hold, position):
        self.tap = tap
        self.hold = hold
        self.config = config
        if hold:

            self.pos = key_to_pos[tap.default] if not position else position
    def compile(self):
        root, generated = self.tap.compile()
        label = self.tap.label + "_key"
        if not self.hold:
            return generated.replace(root[1:], label).replace(root[1:].upper(), label.upper())
        return self.gen_holdtap(label, self.hold, root, self.pos) + "\n" + generated
    def gen_holdtap(self, name, hold, tap, position):
        return f'''
{name}:{name} {{
compatible = "zmk,behavior-hold-tap";
#binding-cells = <2>;
flavor = "balanced";
tapping-term-ms = <{self.config.tapping_term}>;
quick-tap-ms = <{self.config.quick_tap}>;
require-prior-idle-ms = <{self.config.prior_idle}>;
bindings = <{hold}>, <{tap}>;
hold-trigger-key-positions = <{position}>;
hold-trigger-on-release;
label = "{name.upper()}";}};
'''


class Morph:
    def __init__(self, label, prefix, default, mods, modified, keep=False, postfix =""):
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
        prev = self.kp(self.default)
        for (key, value) in self.mapping.items():
            mods_complement = set(modmap.keys()) - {key}
            sink = Morph(self.label, "sink",
                         self.kp(value), mods_complement,
                         self.kp(self.default), True, key)
            sinks.append(sink)
            link = Morph(self.label, "link",
                         prev, [key],
                         self.gen_ref(sink))
            links.append(link)
            prev = self.gen_ref(link)

        return prev,links+sinks


    def kp(self, key):
        return f"&kp {key}"

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
    configdata = data['config']
    def_config = Config(**configdata)
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

        maps.append(HoldTap(cfg, Map(label, mapping.pop("key", label), mapping), hold, mapping.pop("pos", None)))

    return maps

def update(target, content):
    print(f"[modder] Start writing to {target}")
    start = "/*<mods-start>*/"
    end = "/*<mods-end>*/"
    new = []
    target_region = False
    with open(target, "r") as f:
        for line in f.readlines():
            if end in line and target_region:
                for l in content.split("\n"):
                    new.append(l+"\n")
                target_region = False
                new.append(end+"\n")
                continue
            if target_region :
                continue
            if start in line and not target_region:
                target_region = True
                new.append(start+"\n")
                continue
            new.append(line)
    with open(target, "w") as f:
        f.writelines(new)
    print(f"[modder] Done writing to {target}")




def run(origin, target):
    print(f"[modder] Reading {origin}")
    mappings = parse(origin)
    print(f"[modder] Parsed {len(mappings)} mappings")
    content = ""
    for m in mappings:
        content += m.compile() + "\n"
    update(target, content)
# run("C:\\dev\\zmk-config\\shortcuts\\mods.yaml", "C:\\dev\\zmk-config\\config\\glove80.keymap")


#
# a = parse("C:\\dev\\zmk-config\\shortcuts\\mods.yaml")
# for i in a: print(i.compile())