#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat <<'EOF'
使い方: ./scripts/build-firmware.sh [all|right|left|reset] [--update]

引数なしは build.yaml の全構成をビルドします。
--update はキャッシュ済みの依存ソースを更新します。
Docker Desktop を起動してから実行してください。
EOF
}

target=all
update=0
for arg in "$@"; do
    case "$arg" in
        all|right|left|reset) target="$arg" ;;
        --update) update=1 ;;
        -h|--help) usage; exit 0 ;;
        *) usage >&2; exit 2 ;;
    esac
done

if ! command -v docker >/dev/null 2>&1 || ! docker info >/dev/null 2>&1; then
    echo 'Docker Desktop をインストールして起動してください。' >&2
    exit 1
fi

repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
output_dir="$repo_dir/.build/firmware"
cache_file="$repo_dir/.build/build-volume"
cache_volume="${CORCELL_BUILD_VOLUME:-corcell-zmk-build-cache}"
if [[ -z "${CORCELL_BUILD_VOLUME:-}" && -f "$cache_file" ]]; then
    cache_volume="$(cat "$cache_file")"
fi
mkdir -p "$output_dir"

docker run --rm --platform linux/amd64 \
    --mount "type=volume,source=$cache_volume,target=/work" \
    --mount "type=bind,source=$repo_dir,target=/repo,readonly" \
    --mount "type=bind,source=$output_dir,target=/output" \
    --workdir /work \
    zmkfirmware/zmk-build-arm:stable \
    python3 /repo/scripts/build-firmware.py "$target" "$update" \
    2>&1 | tee "$repo_dir/.build/build-firmware.log"

printf '%s\n' "$cache_volume" > "$cache_file"
printf '\n生成先: %s\n'  "$output_dir"
