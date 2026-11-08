#!/usr/bin/env bash
set -euo pipefail

# A executer dans Ubuntu/WSL. Aucun fichier existant n'est supprime ou remplace.
source_dir='/mnt/c/Users/Christopher/Desktop/hackathon-app'
parent_dir="$HOME/projets"
target_dir="$parent_dir/hackathon-app"

if [[ ! -d "$source_dir/.git" ]]; then
  printf 'Le depot source est introuvable : %s\n' "$source_dir" >&2
  exit 1
fi

if [[ -e "$target_dir" || -L "$target_dir" ]]; then
  printf 'La cible existe deja ; aucune copie effectuee : %s\n' "$target_dir" >&2
  exit 1
fi

mkdir -p -- "$parent_dir"
mkdir -- "$target_dir"
cp -a -- "$source_dir/." "$target_dir/"

printf 'Copie creee : %s\n' "$target_dir"
git -C "$target_dir" status --short --branch
