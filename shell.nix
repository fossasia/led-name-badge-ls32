{
  pkgs ? import <nixpkgs> { },
}:

let
  python = pkgs.python3;
in
pkgs.mkShell {
  buildInputs = with pkgs; [
    hidapi
    python
    uv
    darwin.lsusb
  ];

  env = {
    UV_PYTHON_DOWNLOADS = "never";
    DYLD_FALLBACK_LIBRARY_PATH = "${pkgs.lib.makeLibraryPath [ pkgs.hidapi ]}";
  };

  shellHook = ''
    if [ ! -d .venv ]; then
        uv venv --python ${pkgs.lib.getExe python}
    fi
    source .venv/bin/activate
    # macos dependencies
    uv pip install pyhidapi pyusb pillow
  '';
}
