import os
from pathlib import Path

import yaml


def main() -> None:
    modules_path = Path("plugins/modules")
    runtime_path = Path("meta/runtime.yml")
    modules = sorted([module.stem for module in modules_path.glob("*.py")])
    action_groups = {"squeezer": modules}
    runtime = yaml.safe_load(runtime_path.read_text())
    if runtime.get("action_groups") != action_groups:
        print("Updating action groups. 🌓")
        runtime["action_groups"] = action_groups
        runtime_path.write_text(yaml.safe_dump(runtime, explicit_start=True, explicit_end=True))
    else:
        print("Action groups are up to date. 🎬")


if __name__ == "__main__":
    main()
