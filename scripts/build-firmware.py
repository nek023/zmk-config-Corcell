"""Docker 内で build.yaml に従って ZMK をビルドする。"""

import fcntl
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys

import yaml


def run(*args):
    print("+ " + " ".join(args), flush=True)
    subprocess.run(args, check=True)


def main():
    target, update = sys.argv[1:]
    shields = {"right": "corcell_r", "left": "corcell_l", "reset": "settings_reset"}
    matrix = yaml.safe_load(Path("/repo/build.yaml").read_text())["include"]
    entries = [entry for entry in matrix if target == "all" or entry["shield"] == shields[target]]
    if not entries:
        raise SystemExit(f"build.yaml に {target} の構成がありません。")

    # 同じキャッシュを使う並行ビルドによる破損を防ぐ。
    with Path("/work/.build-lock").open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit("同じキャッシュで別のビルドが実行中です。終了後に再実行してください。")

        shutil.rmtree("/work/config", ignore_errors=True)
        shutil.copytree("/repo/config", "/work/config")
        manifest_hash = hashlib.sha256(Path("/work/config/west.yml").read_bytes()).hexdigest()
        stamp = Path("/work/.corcell-manifest-sha256")
        if not Path("/work/.west").exists():
            run("west", "init", "-l", "/work/config")
        if update == "1" or not stamp.exists() or stamp.read_text() != manifest_hash:
            run("west", "update", "--fetch-opt=--filter=tree:0")
            stamp.write_text(manifest_hash)
        run("west", "zephyr-export")
        run("west", "manifest", "--freeze", "--active-only", "-o", "/output/west-frozen.yml")
        shutil.copyfile("/work/config/corcell.keymap", "/output/corcell.keymap")

        for entry in entries:
            shield = entry["shield"]
            build_dir = f"/work/build-{shield}"
            artifact = Path("/output") / (entry["artifact-name"] + ".uf2")
            artifact.unlink(missing_ok=True)
            args = ["west", "build", "-s", "zmk/app", "-d", build_dir, "-b", entry["board"]]
            if entry.get("snippet"):
                args += ["-S", entry["snippet"]]
            args += ["--", "-DZMK_CONFIG=/work/config", f"-DSHIELD={shield}", "-DZMK_EXTRA_MODULES=/repo"]
            run(*args)
            shutil.copyfile(Path(build_dir) / "zephyr/zmk.uf2", artifact)
            # macOS から成果物を編集できる権限にする。
            artifact.chmod(0o644)
            print(f"生成完了: {artifact.name} ({artifact.stat().st_size:,} bytes)", flush=True)


if __name__ == "__main__":
    os.chdir("/work")
    main()
