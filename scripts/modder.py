import re
import string
from itertools import groupby

import yaml
keychars = {
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
    "\2": "PAGE_UP",
    "\3": "PAGE_DOWN",
    "\4": "",
    "\5": "",
    "\6": "",
    "\7": "",
    "\n": "ENTER",
    "\b": "LEFT_ARROW",
    "\t": "TAB",
    "\f": "RIGHT_ARROW",
    "\v": "DOWN_ARROW",
    "\r": "UP_ARROW",
}

keys = {k for k in keychars.values()}
keys |= {f"F{n}" for n in range(25)}
keys |= {f"{m}{k}" for m in ["L", "R", "LEFT_", "RIGHT_"] for k in ["SHIFT", "GUI", "CTRL", "ALT"]}
keys |= {f"{m}{k}" for m in ["", "LEFT_", "RIGHT_"] for k in ["LEFT", "RIGHT", "DOWN", "UP"]}

numlock={
    "0": "KP_NUMBER_0",
    "1": "KP_NUMBER_1",
    "2": "KP_NUMBER_2",
    "3": "KP_NUMBER_3",
    "4": "KP_NUMBER_4",
    "5": "KP_NUMBER_5",
    "6": "KP_NUMBER_6",
    "7": "KP_NUMBER_7",
    "8": "KP_NUMBER_8",
    "9": "KP_NUMBER_9",
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
        layers = [int(l) for l in cfg.pop("layers", [])]
        if isinstance(node, dict):
            if "combo" in node:
                node = node["combo"]
            else :
                node["name"] = name+ "_delegate"
        binding = self.anon_parser.parse(node)
        return Combo(name, pos, binding, layers, **cfg)


class MorphParser:
    def __init__(self, cfg):
        self.anon_parser = None
        self.hold_tap_parser = None
        self.cfg = cfg

    def extract_name_default(self, orig, node):
        node = node.copy()
        name = node.pop("name", None)
        default = node.pop("default", node.pop("d", None))
        if not name and orig:
            if len(orig) <= 2 and orig.isalnum():
                name = orig + "_key"
            elif re.search("[a-zA-Z0-1_]", orig): # use full match
                name = orig
            else:
                name = None
        if not name:
            name = None

        sub_name = ("" if not orig else orig) if not name else name
        if self.hold_tap_parser.is_inline_holdtap(node):
            default = self.anon_parser.parse(node)
        elif default and self.hold_tap_parser.is_inline_holdtap(node | {"tap": default}):
            default = self.anon_parser.parse(node | {"tap": default, "name": sub_name+"_hold_tap"})
        elif orig and self.hold_tap_parser.is_inline_holdtap(node | {"tap": orig}):
            default = self.anon_parser.parse(node | {"tap": orig, "name": sub_name+"_hold_tap"})
        elif default:
            default = self.anon_parser.parse(default)

        if not default and orig:
            default = self.anon_parser.parse(orig)
        elif not default:
            raise Exception(f"Cannot parse {node}: name: {name}, default: {default}")

        return name, default

    def parse(self, name, node):
        cfg = extract_cfg_and_merge(self.cfg, node)
        if isinstance(node, str): return self.parse(name, {"default": node})
        exact = cfg.pop("exact")
        mapping = self.extract_mapping(node)
        name, default = self.extract_name_default(name, node)

        if not mapping:
            mapping = {mod: default for mod in all_mods.keys()}
            exact = False
            cfg["keep"] = "all"
        kept_mods = list(self.keep_mods(set(mapping.keys()), cfg.pop("keep")))


        if exact:
            base_name = default.name() + "_morph" if not name else name
            morph, extra = self.generate_exact(base_name, default, mapping)
            return Morph(name, morph.default, morph.modified, morph.mods, morph.keep), extra

        (modifier, modified) = list(mapping.items())[0]
        return Morph(name, default, modified, list(mapping.keys()), kept_mods), []

    def extract_mapping(self,  node):
        mapping = {}

        if "all" in node:
            filler = self.anon_parser.parse(node["all"])
            for mod in all_mods.keys(): mapping[mod] = filler

        for k in list(node.keys()):
            if k in all_mods.keys():
                mapping[k] = self.anon_parser.parse(node.pop(k))
            if k in wildmods:
                parsed = self.anon_parser.parse(node.pop(k))
                for m in wildmods[k]:
                    mapping[m] = parsed


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

        # if " " in hold.binding():  # to avoid calls like &nav LEFT 1, we just pack it into macro
        #     hold = self.macrosize_hold(hold)
        # if " " in tap.binding():
        #     tap = self.macrosize_tap(tap) # maybe just pass it to the binding of hold tap
        cfg = extract_cfg_and_merge(self.cfg, node)
        positions = node.pop("pos", cfg.pop("positions"))

        return HoldTap(name, hold, tap, self.layout.parse(positions), **cfg)

    def parse_inline(self, node):
        name = node.pop("n", node.pop("name", self.get_name(node)))
        return self.parse(name, node)

    def macrosize_tap(self, node):
        return self.anon_parser.parse([node.binding()])

    def macrosize_hold(self, node):
        return self.anon_parser.parse(
            ["<&macro_press>", node.binding(),
             "<&macro_pause_for_release>",
             "<&macro_release>", node.binding(),
             ]
        )

    def get_name(self, node):
        return None

    def is_inline_holdtap(self, node):
        return isinstance(node, dict) and (("hold" in node or "h" in node) and ("tap" in node or "t" in node))


class KeyParser:
    def is_kp(self, key):
        if not isinstance(key, str): return False
        key = rm_mods(key)
        return (key in keychars or key in keys or re.fullmatch("[A-Z0-9_]+|[ -~\n\t]", key))

    def parse(self, key):
        key = key if key not in keychars else keychars[key]
        return Binding(bind(f"kp {key.upper()}"), clean(key))

def rm_mods(key):
    mods = "[LR][SGCA]\\((.+)\\)"
    key = re.sub(mods, r"\1", key)
    key = re.sub(mods, r"\1", key)
    key = re.sub(mods, r"\1", key)
    return key


class MacroParser:
    def __init__(self, layout, cfg):
        self.layout = layout
        self.key_parser = None
        self.binding_parser = None
        self.default_cfg = cfg

    # not delegating to anon_parser to forbid assigning hold tap or morph to macro
    def parse(self, name, node):
        node = self.layout.preprocess(node)

        if self.is_valid_tap_list(node): return self.parse_tap_list(name, node)
        if self.is_valid_tap_inline(node): return self.parse_tap_inline(name, node)
        if self.is_valid_object(node): return self.parse_object(name, node)
        if self.is_valid_binding_list(node): return self.parse_binding_list(name, node)
        if self.is_valid_binding(node): return self.parse_binding(name, node)
        if self.is_valid_unicode(node): return self.parse_unicode(name, node)
        if self.is_valid_press(node): return self.parse_press(name, node)

        return self.parse_tap_inline(name, node)  # assuming is tap inline by default

    def parse_inline(self, node):
        if self.is_valid_tap_list(node): return self.parse_tap_list(None, node)
        if self.is_valid_tap_inline(node): return self.parse_tap_inline(None, node)
        if self.is_valid_object(node): return self.parse_object(node.pop("n", None), node)
        if self.is_valid_binding_list(node): return self.parse_binding_list(None, node)
        if self.is_valid_binding(node): return self.parse_binding(None, node)
        if self.is_valid_unicode(node): return self.parse_unicode(None, node)
        if self.is_valid_press(node): return self.parse_press(None, node)

        return self.parse_tap_inline(None, node)

    def parse_binding(self, name, node):
        b = self.binding_parser.parse(node)
        arity = 0 + ("macro_param_1" in b.binding()) + ("macro_param_2" in b.binding())
        return Macro(name, [b], arity, **self.default_cfg)

    def parse_binding_list(self, name, ls):
        bindings = [self.binding_parser.parse(v) for v in ls]
        arity = 0 + any(["macro_param_1" in b.binding() for b in bindings]) + any(
            ["macro_param_2" in b.binding() for b in bindings])
        return Macro(name, bindings, arity, **self.default_cfg)

    def parse_tap_inline(self, name, node):
        node = node.removeprefix("{").removesuffix("}") if node.startswith("{") and node.endswith("}") else node
        if len(node) == 1:
            return self.parse_press_inline(name, node)
        if self.key_parser.is_kp(node):
            return self.parse_press_list(name, [node])
        return Macro(name, [self.binding_parser.parse("&macro_tap")] + [self.key_parser.parse(k) for k in node], 0,
                     **self.default_cfg)

    def parse_press(self, name, node):
        target = node.pop("press", node.pop("p", None))
        if self.is_valid_binding(target):
            return self.parse_press_list(name, [target])
        if isinstance(target, list):
            return self.parse_press_list(name, target)
        return self.parse_press_inline(name, target)

    def parse_press_list(self, name, ls):
        keys = [self.key_parser.parse(k)
                if not self.binding_parser.is_binding(k)
                else self.binding_parser.parse(k)
                for k in ls]
        press = self.binding_parser.parse("&macro_press")
        pause = self.binding_parser.parse("&macro_pause_for_release")
        release = self.binding_parser.parse("&macro_release")
        return Macro(name, [press, *keys, pause, release, *keys], 0, **self.default_cfg)

    def parse_press_inline(self, name, node):
        keys = [self.key_parser.parse(k) for k in node]
        press = self.binding_parser.parse("&macro_press")
        pause = self.binding_parser.parse("&macro_pause_for_release")
        release = self.binding_parser.parse("&macro_release")
        return Macro(name, [press, *keys, pause, release, *keys], 0, **self.default_cfg)


    def parse_unicode(self, name, node):
        altcode = "0" + str(ord(node))
        code = " ".join([f"&kp {numlock[n]}" for n in altcode])
        return self.parse_binding_list(name, ["&macro_press","&kp LEFT_ALT", "&macro_tap",code, "&macro_release", "&kp LALT"])

    def parse_tap_list(self, name, ls):
        if len(ls) == 1: return self.parse_press_list(name, ls)
        return Macro(name, [self.binding_parser.parse("&macro_tap")] + [self.key_parser.parse(k) for k in ls], 0,
                     **self.default_cfg)

    def parse_object(self, name, obj):
        macro = self.parse(name, obj.pop("m", obj.pop("macro", None)))
        return Macro(macro._name, macro.bindings, macro.arity, **(self.default_cfg | obj))

    def is_valid_object(self, node):
        return isinstance(node, dict) and (
                "m" in node or "macro" in node)  # {"m": name} or {name : {m: ""}} or {name: ""}


    def is_valid_press(self, node):
        return isinstance(node, dict) and (
                "p" in node or "press" in node)  # {"m": name} or {name : {m: ""}} or {name: ""}


    def is_valid_unicode(self, node):
        return isinstance(node, str) and node not in string.printable and len(node) == 1

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
                self.is_valid_tap_list(node) or
                self.is_valid_unicode(node))


class BindingParser:
    def __init__(self):
        pass

    def is_binding(self, node):
        return isinstance(node, str) and (self.is_full(node) or self.is_short(node))

    def is_short(self, node):
        return (node.startswith("&") and (node.split(" ")[0][1:].isalpha() or "_" in node.split(" ")[0][1:]))

    def is_full(self, node):
        return node.startswith("<&") and node.endswith(">")

    def parse(self, node):
        if self.is_short(node):
            return Binding(bind(node))

        return Binding(node)

def deunderline(name):
    return (name.replace("____", "_").replace("___", "_").replace("__", "_").removeprefix("_").removesuffix(
            "_")).lower()[:40]

def clean(name, backup="unknown"):
    name = rm_mods(name)
    truncated = "_".join([r[:3] for r in name.split("_")]) if len(name) > 10 else name
    result = deunderline(truncated)
    result = backup if len(result) < 3 else result
    return result


def readable(orig):
    binding = rm_mods(orig)
    binding = binding.replace("&macro_pause_for_release", "")
    binding = binding.replace("&macro_release", "")
    binding = binding.replace("&macro_tap", "")
    binding = binding.replace("&macro", "")
    binding = binding.replace("&kp KP_NUMBER_", "")
    nobind = re.sub("[^a-zA-Z0-9_& ]", "", binding)
    result = (nobind if len(nobind) > 2 else re.sub("&([a-zA-Z0-1_]+) ", r"\1_",  binding)).lower()
    return clean(re.sub("[^a-zA-Z0-9_]", "", result.replace(" ", "_")), "")

class Binding:
    def __init__(self, binding, name=None):
        self._binding = binding
        self._name = name if name else readable(binding)

    def binding(self):
        return self._binding

    def name(self):
        return self._name

    def compile(self):
        return ""

    def __str__(self): return self.binding()

    def __repr__(self): return self.binding()


def compile_cfg(**cfg):
    cfg = {k: v for k, v in cfg.items() if v or v == 0}
    def val(v):
        if isinstance(v, list):
            f = v[0]
            if isinstance(f, int):
                return f'<{" ".join([str(i) for i in v])}>'
        if isinstance(v, str): return f'"{v}"'
        return f"<{v}>"
    return " ".join([f"{k} = {val(v)};" if not isinstance(v, bool) else f"{k};" for (k, v) in cfg.items()])


def bind(name):
    return f"<&{name.removeprefix('&')}>"


class Macro:
    def __init__(self, name, bindings, arity=0, **cfg):
        self.bindings = bindings
        self.cfg = cfg
        self.arity = arity
        self._name = self.gen_name(name)
    def gen_name(self, name):
        return name if name else deunderline("_".join([clean(b.name(), "") for b in self.bindings]))

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
    def __init__(self, layout, binder, morph, hold_tap, macro, key_parser, binding):
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
        self.layout = layout

    def parse0(self, node):
        node = self.layout.preprocess(node)

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

wildmods = {
    "ctrl": ["lctrl", "rctrl"],
    "alt": ["ralt", "ralt"],
    "shift": ["lshift", "rshift"],
    "gui": ["lgui", "rgui"],
}

class Layout():
    def __init__(self, layers, left, right):
        self.left = left
        self.right = right
        self.keys = left | right
        self.layers = { "@"+str(l): i for (i,l) in enumerate(layers) }
        print(self.layers)

    def parse(self, positions):
        return list(self.parse_positions(positions.split(" ")))

    def parse_positions(self, positions):
        for pos in positions:
            if pos in self.keys:
                yield self.pos(pos)
            if pos.isnumeric():
                yield int(pos)
            if "left" in pos:
                for v in self.lefts():
                    yield v
            if "right" in pos:
                for v in self.rights():
                    yield v

    def get_layer(self, name):
        return self.layers[name]
    def preprocess(self, node):
        if isinstance(node, str):
            for (layer, index) in self.layers.items():
                if layer in node:
                    new = node.replace(layer, str(index))
                    print(f"Layout preprocessing: replaced {node} with {new}")
                    node = new
        return node

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


class Combo:
    def __init__(self, name, positions, binding, layers, **cfg):
        self.name = name
        self.positions = positions
        self.binding = binding
        self.layers = layers
        self.cfg = cfg

    def compile(self):
        pos = " ".join([p for p in self.positions])
        lay = " ".join([str(l) for l in self.layers])
        return f'''
        {self.name} {{ {compile_cfg(**self.cfg)} key-positions = <{pos}>; layers = <{lay}>;
            bindings = {self.binding.binding()}; 
        }};'''

    def __str__(self): return self.name + " = " + str(self.binding)

    def __repr__(self): return self.name + " = " + str(self.binding)


class HoldTap:
    def __init__(self, name, hold, tap, positions, **cfg):
        self.tap = tap
        self.hold = hold
        self.tapbind, self.taparg = self.parse_binding_arg(tap)
        self.holdbind, self.holdarg = self.parse_binding_arg(hold)
        self._name = self.gen_name(name, hold, tap)
        self.cfg = cfg
        self.positions = positions
        self.cfg["hold-trigger-key-positions"] = self.positions

    def parse_binding_arg(self, binding):
        binding = binding.binding()
        if " " not in binding: return binding, "0"
        bind, arg = tuple(binding.split(" "))
        return bind+">", arg.removesuffix(">")
    def gen_name(self, name, tap, hold):
        return name if name else deunderline("_".join([clean(hold.name()), "x", clean(tap.name())]))
    def binding(self):
        return bind(self._name + f" {self.holdarg} {self.taparg}")
    def name(self):
        return self._name
    def compile(self):
        return f'''
        {self._name}:{self._name} {{ label = "{self._name.upper()}"; #binding-cells = <2>; compatible = "zmk,behavior-hold-tap";  
            {compile_cfg(**self.cfg)}
            bindings = {self.holdbind}, {self.tapbind};
        }};'''

    def __str__(self): return self._name + " = " + str(self.tap) + " / " + str(self.hold)

    def __repr__(self): return self._name + " = " + str(self.tap) + " / " + str(self.hold)


class Morph:
    def __init__(self, name, default, modified, mods, keep):
        self.default = default
        self.mods = mods
        self.modified = modified
        self._name = self.gen_name(name)
        self.keep = keep

    def map_mods(self, mods_ls):
        return "|".join([all_mods[m] for m in sorted(mods_ls)])

    def gen_name(self, name):
        return name if name else deunderline("_".join([clean(self.default.name()), "or", clean(self.modified.name())]))


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

def parse_yaml(file):
    data = read(file)
    pos = Layout(data["layers"], **data['keys'])

    combod = data["combo"]
    combocfg = combod.pop("config")

    macrod = data["macro"]
    macrocfg = macrod.pop("config")

    htd = data["hold-tap"]
    htcfg = htd.pop("config")

    morphd = data["morph"]
    morphcfg = morphd.pop("config")

    binder = NodeBinder()
    morph = MorphParser(morphcfg)
    hold_tap = HoldTapParser(htcfg, pos)
    macro = MacroParser(pos, macrocfg)
    key = KeyParser()
    binding = BindingParser()
    parser = AnonymousNodeParser(pos, binder, morph, hold_tap, macro, key, binding)

    combo = ComboParser(pos, parser, **combocfg)

    combos = [combo.parse(name, v) for (name, v) in combod.items()]
    print(f"[modder] Parsed {len(combos)} combos")
    macros = [macro.parse(name, v) for (name, v) in macrod.items()]
    print(f"[modder] Parsed {len(macros)} macros")

    hts = [hold_tap.parse(name, v) for (name, v) in htd.items()]
    print(f"[modder] Parsed {len(hts)} hold taps")

    morphspairs = [morph.parse(name, v) for (name, v) in morphd.items()]
    morphs = []
    for (o, extra) in morphspairs:
        morphs.append(o)
        morphs += extra

    print(f"[modder] Parsed {len(morphs)} morphs")

    nodes = list(binder.nodes.values())
    print(f"[modder] Generated {len(nodes)} nodes")

    all = combos + macros + hts + morphs + nodes
    group = {k: list(g) for k, g in groupby(sorted(all, key = lambda x: str(type(x))), lambda x: type(x))}
    return group.pop(Binding, []), group.pop(Combo, []), group.pop(HoldTap, []), group.pop(Morph, []), group.pop(Macro, [])

def read(file):
    with open(file, "r", encoding="utf-8") as f:
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
    bindings, combos, holdtaps, morphs, macros = parse_yaml(origin)

    update(target, compile(holdtaps+morphs), "/*<mods-start>*/", "/*<mods-end>*/")
    update(target, compile(combos), "/*<combos-start>*/", "/*<combos-end>*/")
    update(target, compile(macros), "/*<macros-start>*/", "/*<macros-end>*/")
    return bindings, combos, holdtaps, morphs, macros


def compile(compilable_list):
    return "\n".join([m.compile() for m in compilable_list])

def run(origin, target):
    return run0(origin, target)

#bindings, combos, holdtaps, morphs, macros = run("C:\\dev\\zmk-config\\shortcuts\\mods.yaml", "C:\\dev\\zmk-config\\config\\glove80.keymap")
