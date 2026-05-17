{ pkgs }: {
  deps = [
    pkgs.python311
    pkgs.python311Packages.pip
    pkgs.glibcLocales
  ];
  env = {
    PYTHONIOENCODING = "utf-8";
    LANG = "ko_KR.UTF-8";
  };
}
