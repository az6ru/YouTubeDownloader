{ pkgs }: {
  deps = [
    pkgs.python3
    pkgs.python3Packages.pip
    pkgs.postgresql
    pkgs.openssl
  ];

  shellHook = ''
    pip install flask requests psycopg2-binary
  '';
}
