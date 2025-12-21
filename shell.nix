{ pkgs, ... }:
pkgs.mkShell {
  packages = with pkgs; [
    uv
  ];

  env = {
    UV_PYTHON = "${pkgs.python313}/bin/python";

    LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath (
      with pkgs;
      [
        stdenv.cc.cc.lib
      ]
    );
  };

  shellHook = ''
    export PATH=$PWD/.venv/bin/:$PATH
  '';
}
