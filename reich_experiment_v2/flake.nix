{
  description = "Reich Neandertal pulse / reciprocal epistasis reproducible experiment";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" ];
      forAllSystems = f: nixpkgs.lib.genAttrs systems (system: f system);
    in {
      devShells = forAllSystems (system:
        let
          pkgs = import nixpkgs { inherit system; };
          python = pkgs.python3.withPackages (p: with p; [ numpy matplotlib ]);
        in {
          default = pkgs.mkShell { packages = [ python ]; };
        });
    };
}
