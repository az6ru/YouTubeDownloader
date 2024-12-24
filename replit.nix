{ pkgs }: {
  deps = [
    pkgs.python3
    pkgs.python3Packages.pip
  ];

  shellHook = ''
    pip install -r requirements.txt
  '';
}
