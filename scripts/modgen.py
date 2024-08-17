
map = {
    "G" : "X",
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
    print(res + "\n")
for (k, v) in map.items():
    gen(k, v)