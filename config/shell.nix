{ pkgs ? ( import /src/nix/pinned-nixpkgs.nix {})}:
let
  packageOverrides = pkgs.callPackage ./python-packages.nix { };
  python = pkgs.python3.override { inherit packageOverrides; };
  pythonWithPackages = python.withPackages (ps: [
  ps.keymap-drawer
  ps.typing-extensions
  ps.tree-sitter
  ps.tree-sitter-devicetree
  ps.pyyaml
  ps.python-dotenv
  ps.pydantic-settings ps.pydantic-core
  ps.pydantic
  ps.platformdirs
  ps.pcpp
  ps.annotated-types
  ps.tree-sitter
  ]);
in
pkgs.mkShell {
  nativeBuildInputs = [ pythonWithPackages ];
}