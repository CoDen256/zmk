

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
        m = list(map(lambda x: modmap[x], self.mods))
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

a = Map("C", {"lshift" : "LC(Z)", "rctrl": "RC(F14)"})
r = a.generate()
(prev,gen) = a.compile()
print(gen)
print(prev)

mapp = {
    "" : "X",
    "H" : "V",
    "I" : "S",
    "U" : "Z",
    "K" : "A",
    "Q" : "Y"
}
def gen(key, trg):

    res = f'''
{key}_key:{key}_key {{
    compatible = "zmk,behavior-hold-tap";
    #binding-cells = <2>;
    flavor = "balanced";
    tapping-term-ms = <280>;
    quick-tap-ms = <175>;
    require-prior-idle-ms = <350>;
    bindings = <&kp>, <&{key}nomods>;
    hold-trigger-key-positions = <28 29 30 31 32 40 41 42 43 44 58 59 60 61 62 75 76 77 78 79 69 70 71 72 73 74>;
    hold-trigger-on-release;
    label = "{key}_KEY";}};

{key}nomods:{key}nomods {{
    compatible = "zmk,behavior-mod-morph";

#binding-cells = <0>;
bindings = <&kp {key}>, <&{key}lctrl>;
label = "{key}NOMODS";
mods = <(MOD_LCTL)>;
keep-mods = <(MOD_LCTL)>;}};

{key}lctrl:{key}lctrl {{
    compatible = "zmk,behavior-mod-morph";

#binding-cells = <0>;
bindings = <&kp {trg}>, <&kp {key}>;
label = "{key}LCTRL";
mods = <(MOD_LSFT|MOD_LALT|MOD_LGUI|MOD_RCTL|MOD_RSFT|MOD_RALT|MOD_RGUI)>;
keep-mods = <(MOD_RCTL|MOD_LGUI|MOD_LALT|MOD_LSFT|MOD_RALT|MOD_RSFT|MOD_RGUI)>;}};
'''
    # print(res + "\n")
# for (k, v) in mapp.items():
#     gen(k, v)