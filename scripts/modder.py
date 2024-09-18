import random
import re
import string

import yaml


def rnd(n: int):
    return bytes(random.choices(string.ascii_uppercase.encode('ascii'), k=n)).decode('ascii')


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
    "\0": "END",
    "\1": "HOME",
    "\2": "KP_N2",
    "\3": "KP_N3",
    "\4": "KP_N4",
    "\5": "KP_N5",
    "\6": "KP_N6",
    "\7": "KP_N7",
    "\n": "ENTER",
    "\b": "LEFT_ARROW",
    "\f": "RIGHT_ARROW",
    "\v": "DOWN_ARROW",
    "\r": "UP_ARROW",
}


def extract_cfg_and_merge(default, target):
    cfg = default.copy()
    if isinstance(target, dict):
        for p in cfg.keys():
            if p in target:
                cfg[p] = target.pop(p)  # extract only relevant config properties
    return cfg


class ComboParser:
    def __init__(self, layout, anon_parser, **cfg):
        self.anon_parser = anon_parser
        self.layout = layout
        self.default_cfg = cfg

    def parse(self, name, node):
        pos = [str(self.layout.pos(k)) for k in list(name)]
        cfg = extract_cfg_and_merge(self.default_cfg, node)
        if isinstance(node, dict):
            if "combo" in node:
                node = node["combo"]
        binding = self.anon_parser.parse(node)
        return Combo(name, pos, binding, **cfg)


class MorphParser:
    def __init__(self, cfg):
        self.anon_parser = None
        self.hold_tap_parser = None
        self.cfg = cfg

    def get_name(self, node):
        return rnd(10)

    def extract_name_default(self, orig, node):
        node = node.copy()
        name = node.pop("name", None)
        default = node.pop("default", node.pop("d", None))
        if default: default = self.anon_parser.parse(default)

        if not name and orig:
            if len(orig) == 1 and orig.isalpha():
                name = orig + "_key"
            elif orig.isalnum():
                name = orig
            else:
                name = rnd(10)
        if not name:
            name = rnd(10)

        if self.hold_tap_parser.is_inline_holdtap(node):
            default = self.hold_tap_parser.parse_inline(node)

        if self.hold_tap_parser.is_inline_holdtap(node | {"tap": orig}):
            default = self.hold_tap_parser.parse_inline(node | {"tap": orig})

        if not default and orig:
            default = self.anon_parser.parse(orig)
        elif not default:
            default = self.anon_parser.parse(default)

        return name, default

    def parse(self, name, node):
        cfg = extract_cfg_and_merge(self.cfg, node)
        exact = cfg.pop("exact")
        mapping = self.extract_mapping(node)
        name, default = self.extract_name_default(name, node)

        if not mapping: return {mod: default for mod in all_mods.keys()}
        kept_mods = list(self.keep_mods(set(mapping.keys()), cfg.pop("keep")))


        if exact:
            morph, extra = self.generate_exact(name, default, mapping)
            return Morph(name, morph.default, morph.modified, morph.mods, morph.keep), extra

        (modifier, modified) = list(mapping.items())[0]
        return Morph(name, default, modified, list(mapping.keys()), kept_mods)

    def extract_mapping(self,  node):
        mapping = {}
        if "all" in node:
            filler = self.anon_parser.parse(node["all"])
            for mod in all_mods.keys(): mapping[mod] = filler

        for k in list(node.keys()):
            if k in all_mods.keys(): mapping[k] = self.anon_parser.parse(node.pop(k))


        return mapping


    def complement(self, keys):
        return set(all_mods.keys()) - keys

    def keep_mods(self, origin, keeps):
        for k in keeps.split(","):
            if k == "specified":
                for m in origin: yield m
            if k == "all":
                for m in all_mods.keys(): yield m
            if k == "none": pass
            if k == "inverted":
                for c in self.complement(origin): yield c
            if k in all_mods.keys(): yield k

    def generate_exact(self, name, default, mapping):
        sinks = []
        links = []
        prev = default
        for (modifier, modified) in mapping.items():
            mods_complement = self.complement({modifier})
            sink = Morph(name + "_" + modifier + "_sink", modified, default, mods_complement, mods_complement)
            sinks.append(sink)
            link = Morph(name + "_" + modifier + "_link", prev, sink, [modifier], [])
            links.append(link)
            prev = link

        return links.pop(), links + sinks

    def parse_inline(self, node):
        return self.parse(None, node)

    def is_inline_morph(self, node):
        return isinstance(node, dict) and ("d" in node or "default" in node)  # or {key : {"lctrl" : "stuff"# }}


class HoldTapParser:
    def __init__(self, cfg, layout):
        self.anon_parser = None
        self.cfg = cfg
        self.layout = layout

    def parse(self, name, node):
        hold = self.anon_parser.parse(node.pop("h", node.pop("hold", None)))
        tap = self.anon_parser.parse(node.pop("t", node.pop("tap", None)))

        if " " in hold.binding():  # to avoid calls like &nav LEFT 1, we just pack it into macro
            hold = self.macronize(hold)
        if " " in tap.binding():
            tap = self.macronize(tap)
        cfg = extract_cfg_and_merge(self.cfg, node)
        positions = node.pop("pos", cfg.pop("positions"))

        return HoldTap(name, hold, tap, self.layout.parse(positions), **cfg)

    def parse_inline(self, node):
        name = node.pop("n", node.pop("name", self.get_name(node)))
        return self.parse(name, node)

    def macronize(self, node):
        return self.anon_parser.parse([node.binding()])

    def get_name(self, node):
        return rnd(10)

    def is_inline_holdtap(self, node):
        return isinstance(node, dict) and (("hold" in node or "h" in node) and ("tap" in node or "t" in node))


class KeyParser:
    def is_kp(self, key):
        return isinstance(key, str) and re.match("[LR][SGCA]\\([A-Z0-9_]+\\)|[A-Z0-9_]+|.", key)

    def parse(self, key):
        key = key if key not in keynames else keynames[key]
        return Binding(key, bind(f"kp {key.upper()}"))


class MacroParser:
    def __init__(self, cfg):
        self.key_parser = None
        self.binding_parser = None
        self.default_cfg = cfg

    # not delegating to anon_parser to forbid assigning hold tap or morph to macro
    def parse(self, name, node):
        if self.is_valid_tap_list(node): return self.parse_tap_list(name, node)
        if self.is_valid_tap_inline(node): return self.parse_tap_inline(name, node)
        if self.is_valid_object(node): return self.parse_object(name, node)
        if self.is_valid_binding_list(node): return self.parse_binding_list(name, node)
        if self.is_valid_binding(node): return self.parse_binding(name, node)

        return self.parse_tap_inline(name, node)  # assuming is tap inline by default

    def parse_inline(self, node):
        if self.is_valid_tap_list(node): return self.parse_tap_list(self.get_tap_list_name(node), node)
        if self.is_valid_tap_inline(node): return self.parse_tap_inline(self.get_tap_inline_name(node), node)
        if self.is_valid_object(node): return self.parse_object(self.get_object_name(node), node)
        if self.is_valid_binding_list(node): return self.parse_binding_list(self.get_binding_list_name(node), node)
        if self.is_valid_binding(node): return self.parse_binding(self.get_binding_name(node), node)

        return self.parse_tap_inline(self.get_tap_inline_name(node), node)

    def get_tap_list_name(self, node):
        return rnd(10)

    def get_tap_inline_name(self, node):
        return rnd(10)

    def get_object_name(self, node):
        return node.pop("n", rnd(10))

    def get_binding_list_name(self, node):
        return rnd(10)

    def get_binding_name(self, node):
        return rnd(10)

    def parse_binding(self, name, node):
        return Macro(name, self.binding_parser.parse(node), 0, **self.default_cfg)

    def parse_binding_list(self, name, ls):
        bindings = [self.binding_parser.parse(v) for v in ls]
        arity = 0 + any(["macro_param_1" in b.binding() for b in bindings]) + any(
            ["macro_param_2" in b.binding() for b in bindings])
        return Macro(name, bindings, arity, **self.default_cfg)

    def parse_tap_inline(self, name, node):
        node = node.removeprefix("{").removesuffix("}") if node.startswith("{") and node.endswith("}") else node
        return Macro(name, [self.binding_parser.parse("<&macro_tap>")] + [self.key_parser.parse(k) for k in node], 0,
                     **self.default_cfg)

    def parse_tap_list(self, name, ls):
        return Macro(name, [self.binding_parser.parse("<&macro_tap>")] + [self.key_parser.parse(k) for k in ls], 0,
                     **self.default_cfg)

    def parse_object(self, name, obj):
        macro = self.parse(name, obj.pop("m", obj.pop("macro", None)))
        return Macro(macro._name, macro.bindings, macro.arity, **(self.default_cfg | obj))

    def is_valid_object(self, node):
        return isinstance(node, dict) and (
                "m" in node or "macro" in node)  # {"m": name} or {name : {m: ""}} or {name: ""}

    def is_valid_binding(self, node):
        return isinstance(node, str) and self.binding_parser.is_binding(node)

    def is_valid_binding_list(self, node):
        return isinstance(node, list) and all([self.is_valid_binding(l) for l in node])

    def is_valid_tap_list(self, node):
        return isinstance(node, list) and not self.is_valid_binding_list(node)

    def is_valid_tap_inline(self, node):
        return isinstance(node, str) and node.startswith("{") and node.endswith("}")

    def is_inline_macro(self, node):
        return (self.is_valid_binding_list(node) or
                self.is_valid_object(node) or
                self.is_valid_tap_inline(node) or
                self.is_valid_tap_list(node))


class BindingParser:
    def __init__(self):
        pass

    def is_binding(self, node):
        return isinstance(node, str) and (self.is_full(node) or self.is_short(node))

    def is_short(self, node):
        return (node.startswith("&") and (node[1:].isalpha() or "_" in node[1:]))

    def is_full(self, node):
        return node.startswith("<&") and node.endswith(">")

    def parse(self, node):
        if self.is_short(node):
            return Binding(rnd(10), bind(node))

        return Binding(rnd(10), node)


class Binding:
    def __init__(self, name, binding):
        self._binding = binding
        self._name = name

    def binding(self):
        return self._binding

    def name(self):
        return self._name

    def compile(self):
        return ""

    def __str__(self): return self.binding()

    def __repr__(self): return self.binding()


def compile_cfg(**cfg):
    cfg = {k: v for k, v in cfg.items() if v}
    return " ".join([f"{k} = <{v}>;" if not isinstance(v, bool) else f"{k};" for (k, v) in cfg.items()])


def bind(name):
    return f"<&{name.removeprefix("&")}>"


class Macro:
    def __init__(self, name, bindings, arity=0, **cfg):
        self._name = name
        self.bindings = bindings
        self.cfg = cfg
        self.arity = arity


    def name(self):
        return self._name

    def binding(self):
        return bind(self._name)

    def compile(self):
        bindings = ", ".join([b.binding() for b in self.bindings])
        compatible = ["behavior-macro", "behavior-macro-one-param", "behavior-macro-two-param"][self.arity]
        return f'''
        {self._name}: {self._name} {{ label = "{self._name.upper()}"; #binding-cells = <{self.arity}>; compatible = "zmk,{compatible}"; 
            {compile_cfg(**self.cfg)}
            bindings = {bindings};
        }};'''

    def __str__(self): return self.binding() + " = " + str(self.bindings)

    def __repr__(self): return self.binding() + " = " + str(self.bindings)


class AnonymousNodeParser:
    def __init__(self, binder, morph, hold_tap, macro, key_parser, binding):
        self.binding_parser = binding
        self.key_parser = key_parser
        self.macro_parser = macro
        macro.key_parser = key_parser
        morph.anon_parser = self
        morph.hold_tap_parser = hold_tap
        macro.binding_parser = binding
        hold_tap.anon_parser = self

        self.hold_tap_parser = hold_tap

        self.morph_parser = morph
        self.binder = binder

    def parse0(self, node):
        if self.macro_parser.is_inline_macro(node):
            return self.macro_parser.parse_inline(node)

        if self.binding_parser.is_binding(node):
            return self.binding_parser.parse(node)

        if self.key_parser.is_kp(node):
            return self.key_parser.parse(node)

        if isinstance(node, dict):
            if self.morph_parser.is_inline_morph(node):
                return self.morph_parser.parse_inline(node)
            if self.hold_tap_parser.is_inline_holdtap(node):
                return self.hold_tap_parser.parse_inline(node)

        return self.macro_parser.parse_inline(node)

    def parse(self, node):
        node = self.parse0(node)
        if isinstance(node, tuple):
            node, extra = node
            for n in extra:
                self.binder.bind(n)

        self.binder.bind(node)
        return node


class NodeBinder():
    def __init__(self):
        self.nodes = {node.binding(): node for node in []}

    def bind(self, node):
        self.nodes[node.binding()] = node


def kp(key):
    if key in keynames:
        return keynames[key]
    return key


class MacroNode():

    def __init__(self, seq, name=None):
        self.seq = seq.removeprefix("^")
        self._name = name

    def __str__(self):
        return f"{self.seq}"

    def __repr__(self):
        return f"{self.seq}"

    def sequence_binding(self):
        return (self.seq, True) if self.seq.startswith("<&") and self.seq.endswith(">") else (
            [kp(k) for k in self.seq], False)

    def name(self):
        if self._name: return self._name
        return ("_".join([k[4:].lower() for k in self.sequence_binding()[0]]))

    def node(self):
        return "&" + self.name()

    def compile(self):
        binding, custom = self.sequence_binding()
        seq = f"<&macro_tap>, <{' '.join(binding)}>" if not custom else binding
        return f'''
        {self.name()}: {self.name()} {{ label = "{self.name().upper()}"; compatible = "zmk,behavior-macro"; 
            #binding-cells = <0>; #tap-ms = <0>; #wait-ms = <0>;
            bindings = {seq};
        }};'''


class Binder():

    def __init__(self, layout, macros, cfg):
        self._macros = {m.seq: m for m in macros}
        self._hts = {}
        self.layout = layout
        self.cfg = cfg

    def macros(self):
        return self._macros.values()

    def hts(self):
        return self._hts.values()

    def get_macros(self, seq):
        if seq in self._macros:
            return self._macros[seq].node()
        macro = MacroNode(seq)
        self._macros[seq] = macro
        return macro.node()

    def get_holdtap(self, tap, hold, config):
        map = Map(self, self.name(tap), tap, {"lctrl": tap})
        ht = HoldTapNode(self.layout, config, map, hold, None)

        if ht.label() in self._hts:
            return self._hts[ht.label()]
        self._hts[ht.label()] = ht
        return "&" + ht.label() + " 0 0"

    def name(self, keys):
        return ("_".join([kp(k)[4:].lower() for k in keys]))

    def binding(self, key):
        if not key: return "&none"
        if len(key) == 1: return kp(key)
        if key[0] == "&" and key[1].isalpha():
            return key
        if key[0] == "^" and key[1].isalnum():
            return self.get_macros(key[1:])
        if key.startswith("t:") and " h:" in key:
            cfg = self.cfg
            tap, hold = tuple(key.removeprefix("t:").split(" h:"))
            if " c:" in hold:
                hold, cfg = tuple(hold.split(" c:"))
                t, q, r = tuple(cfg.split(","))
                cfg = Config(int(t), int(q), int(r))
            return self.get_holdtap(tap, self.binding(hold), cfg)
        if key[0].isalnum():
            return kp(key)
        # must be macros
        return self.get_macros(key)


all_mods = {
    "lalt": "MOD_LALT",
    "ralt": "MOD_RALT",
    "lctrl": "MOD_LCTL",
    "rctrl": "MOD_RCTL",
    "lgui": "MOD_LGUI",
    "rgui": "MOD_RGUI",
    "lshift": "MOD_LSFT",
    "rshift": "MOD_RSFT",
}


class Layout():
    def __init__(self, left, right):
        self.left = left
        self.right = right
        self.keys = left | right

    def parse(self, positions):
        return list(self.parse_positions(positions.split(" ")))

    def parse_positions(self, positions):
        for pos in positions:
            if len(pos) == 1 and pos.isalpha():
                yield self.pos(pos)
            if pos.isnumeric():
                yield int(pos)
            if "left" in pos:
                for v in self.lefts():
                    yield v
            if "right" in pos:
                for v in self.rights():
                    yield v

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
    def __init__(self, name, positions, binding, **cfg):
        self.name = name
        self.positions = positions
        self.binding = binding
        self.cfg = cfg

    def compile(self):
        pos = " ".join([p for p in self.positions])
        return f'''
        {self.name} {{ {compile_cfg(**self.cfg)} key-positions = <{pos}>;
            bindings = {self.binding.binding()}; 
        }};'''

    def __str__(self): return self.name + " = " + str(self.binding)

    def __repr__(self): return self.name + " = " + str(self.binding)


class ComboNode:
    def __init__(self, layout, binder, pos, out, cfg):
        self.layout = layout
        self.out = out
        self.binder = binder
        self.key_names = pos
        self.pos = " ".join([str(layout.pos(k)) for k in list(pos)])
        self.cfg = cfg

    def compile(self):
        return f'''
        {self.key_names} {{ timeout-ms = <{self.cfg.timeout}>; key-positions = <{self.pos}>;
            bindings = <{self.binder.binding(self.out)}>; 
        }};'''


class Config:
    def __init__(self, tapping_term, quick_tap, prior_idle):
        self.tapping_term = tapping_term
        self.quick_tap = quick_tap
        self.prior_idle = prior_idle


class HoldTapNode:
    def __init__(self, layout, config, tap, hold, position):
        self.tap = tap
        self.hold = hold
        self.config = config
        self.layout = layout
        if hold:
            self.pos = layout.opposite_side(tap.key) if not position else list(
                map(lambda k: layout.pos(k), position.split(" ")))

    def label(self):
        return self.tap._name + "_key" if len(self.tap._name) == 1 else self.tap._name

    def compile(self):
        root, generated = self.tap.compile()
        label = self.label()

        if not self.hold:
            return generated.replace(root[1:], label).replace(root[1:].upper(), label.upper())
        return self.gen_holdtap(label, self.hold, root, self.pos) + "\n" + generated

    def gen_holdtap(self, name, hold, tap, position):
        join = ' '.join(map(lambda x: str(x), position))
        term = self.config.tapping_term
        quick_tap = self.config.quick_tap
        idle = self.config.prior_idle
        return f'''
        {name}:{name} {{ label = "{name.upper()}"; compatible = "zmk,behavior-hold-tap";  
            flavor = "balanced"; hold-trigger-on-release; #binding-cells = <2>; hold-trigger-key-positions = <{join}>;
            tapping-term-ms = <{term}>; quick-tap-ms = <{quick_tap}>; require-prior-idle-ms = <{idle}>;
            bindings = <{hold}>, <{tap}>;
        }};'''


class HoldTap:
    def __init__(self, name, hold, tap, positions, **cfg):
        self._name = name
        self.tap = tap
        self.hold = hold
        self.cfg = cfg
        self.positions = positions
        self.cfg["hold-trigger-key-positions"] = " ".join([str(p) for p in self.positions])

    def binding(self):
        return bind(self._name + " 0 0")
    def name(self):
        return self._name
    def compile(self):
        return f'''
        {self._name}:{self._name} {{ label = "{self._name.upper()}"; #binding-cells = <2>; compatible = "zmk,behavior-hold-tap";  
            {compile_cfg(**self.cfg)}
            bindings = {self.hold.binding()}, {self.tap.binding()};
        }};'''

    def __str__(self): return self._name + " = " + str(self.tap) + " / " + str(self.hold)

    def __repr__(self): return self._name + " = " + str(self.tap) + " / " + str(self.hold)


class Morph:
    def __init__(self, name, default, modified, mods, keep):
        self._name = name
        self.default = default
        self.mods = mods
        self.modified = modified
        self.keep = keep

    def map_mods(self, mods_ls):
        return [all_mods[m] for m in mods_ls]


    def name(self):
        return self._name

    def binding(self):
        return bind(self._name)

    def compile(self):
        label = self._name
        compiled_mods = f"<({self.map_mods(self.mods)})>"
        compiled_keep_mods = f"keep-mods = <({self.map_mods(self.keep)})>;" if self.keep else ""
        return f"""
        {label}:{label} {{ label = "{label.upper()}"; compatible = "zmk,behavior-mod-morph"; #binding-cells = <0>;
            bindings = {self.default.binding()}, {self.modified.binding()};
            mods = {compiled_mods};
            {compiled_keep_mods}
        }};"""

    def __str__(self): return self._name + " ~ " + str(self.default) + " / " + str(self.modified)

    def __repr__(self): return self._name + " ~ " + str(self.default) + " / " + str(self.modified)


class MorphNode:
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
        m = sorted(list(map(lambda x: mods[x], self.mods)))
        joined = "|".join(m)
        mods = f"<({joined})>"
        keep_mods = f"keep-mods = {mods};" if self.keep else ""
        return f"""
        {label}:{label}{{ label = "{label.upper()}"; compatible = "zmk,behavior-mod-morph";
            #binding-cells = <0>;
            bindings = <{self.default}>, <{self.modified}>;
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
            mods_complement = set(all_mods.keys()) - {key}
            sink = MorphNode(self.label, "sink",
                             self.binder.binding(value), mods_complement,
                             self.binder.binding(self.default), True, key)
            sinks.append(sink)
            link = MorphNode(self.label, "link",
                             prev, [key],
                             self.gen_ref(sink))
            links.append(link)
            prev = self.gen_ref(link)

        return prev, links + sinks

    def gen_ref(self, morph):
        return f"&{morph._name()}"

    def compile(self):
        c = ""
        prev, r = self.generate()
        for i in r:
            c += i.compile() + "\n"
        return prev, c


# Function to parse the YAML content and create the list of Map objects
def parse(file):
    # Parse the YAML content
    data = read(file)

    # Create the list of Map objects
    configdata = data['config']
    def_config = Config(**configdata)
    pos = Layout(**data['keys'])

    macros = []
    for (name, seq) in data['macros'].items():
        macros.append(MacroNode(seq, name))

    binder = Binder(pos, macros, def_config)

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
        maps.append(HoldTapNode(pos, cfg, map, hold, mapping.pop("pos", None)))

    combos = []
    combodef = data['combos']
    default = combodef.pop("timeout")
    for (src, out) in combodef.items():
        timeout = default
        if "timeout: " in out:
            out, timeout = out.split("timeout: ")
        combos.append(ComboNode(pos, binder, src, out, ComboCfg(int(timeout))))
    return maps, combos, binder


def read(file):
    with open(file, "r") as f:
        data = yaml.safe_load(f.read())
    return data


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
    hts = binder.hts()
    print(f"[modder] Generated {len(hts)} holdtaps")
    print(hts)
    macroscontent = "\n".join([m.compile() for m in macros])
    content += "\n".join([m.compile() for m in hts])

    update(target, content, "/*<mods-start>*/", "/*<mods-end>*/")
    update(target, combocontent, "/*<combos-start>*/", "/*<combos-end>*/")
    update(target, macroscontent, "/*<macros-start>*/", "/*<macros-end>*/")


def run(origin, target):
    return run0(origin, target)


data = read("C:\\Users\\dchernyshov\\ome\\zmk-config\\shortcuts\\mods.yaml")
pos = Layout(**data['keys'])
combod = data["combo"]
combocfg = combod.pop("config")
macrod = data["macro"]
macrocfg = macrod.pop("config")
htd = data["hold-tap"]
htcfg = htd.pop("config")

morphd = data["map"]
morphcfg = morphd.pop("config")
b = NodeBinder()
morph = MorphParser(morphcfg)
hold_tap = HoldTapParser(htcfg, pos)
macro = MacroParser(macrocfg)
key = KeyParser()
binding = BindingParser()
a = AnonymousNodeParser(b, morph, hold_tap, macro, key, binding)

c = ComboParser(pos, a, **combocfg)
# combos = [c.parse(name, v) for (name, v) in combod.items()]
# macros = [macro.parse(name, v) for (name, v) in macrod.items()]
# hts = [hold_tap.parse(name, v) for (name, v) in htd.items()]
morphs = [morph.parse(name, v) for (name, v) in morphd.items()]

# run("C:\\dev\\zmk-config\\shortcuts\\mods.yaml", "C:\\dev\\zmk-config\\config\\glove80.keymap")


#
# a = parse("C:\\dev\\zmk-config\\shortcuts\\mods.yaml")
# for i in a: print(i.compile())
