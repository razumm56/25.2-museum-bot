{ pkgs, ... }:
pkgs.mkShell {
  packages = with pkgs; [
    uv
  ];

  env = {
    UV_PYTHON = "${pkgs.python313}/bin/python";
  };
}
