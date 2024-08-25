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

class Morph:
    def __init__(self, parent, prefix, default, mods, modified, keep=False, postfix = ""):
        self.parent = parent
        self.prefix = prefix
        self.postfix = postfix if postfix else f"{'_'.join(mods)}"
        self.default = default
        self.mods = mods
        self.modified = modified
        self.keep = keep

    def name(self):
        return f"{self.parent}_{self.prefix}_{self.postfix}"
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
    def __init__(self, default, mapping):
        self.default = default
        self.mapping = mapping
    def generate(self):
        sinks = []
        links = []
        prev = self.kp(self.default)
        for (key, value) in self.mapping.items():
            mods_complement = set(modmap.keys()) - {key}
            sink = Morph(self.default, "sink",
                         self.kp(value), mods_complement,
                         self.kp(self.default), True, key)
            sinks.append(sink)
            link = Morph(self.default, "link",
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
def parse_yaml_to_maps(file):
    # Parse the YAML content
    with open(file, "r") as f:
        data = yaml.safe_load(f.read())

    # Create the list of Map objects
    maps = [Map(name, mappings) for name, mappings in data['map'].items()]

    return maps

def update(target, content):
    print(f"Start writing to {target}")
    start = "/*<mods-start>/*"
    end = "/*<mods-end>/*"
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
    print(f"Done writing to {target}")

# Example YAML content
file = "C:\\dev\\zmk-config\\shortcuts\\mods.yaml"

def run(origin, target):
    print(f"Reading {origin}")
    mappings = parse_yaml_to_maps(origin)
    print(f"Parsed {len(mappings)} mappings")
    content = ""
    for m in mappings:
        content += m.compile()[1] + "\n"
    update(target, content)

run(file, "C:\\dev\\zmk-config\\config\\glove80.keymap")