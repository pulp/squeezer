import getopt
import sys
from pathlib import Path

import yaml


def main(check: bool) -> None:
    modules_path = Path("plugins/modules")
    runtime_path = Path("meta/runtime.yml")
    modules = sorted([module.stem for module in modules_path.glob("*.py")])
    action_groups = {"squeezer": modules}
    runtime = yaml.safe_load(runtime_path.read_text())
    if runtime.get("action_groups") != action_groups:
        if check:
            print("plugins/modules/ and meta/runtime.yml action_groups are not in sync 🌓")
            sys.exit(1)
        else:
            print("Updating action groups. 🌓")
            runtime["action_groups"] = action_groups
            runtime_path.write_text(yaml.safe_dump(runtime, explicit_start=True, explicit_end=True))
    else:
        print("Action groups are up to date. 🎬")


if __name__ == "__main__":
    optlist, args = getopt.getopt(sys.argv[1:], "", ["check"])
    if args:
        print("Too many arguments!")
        sys.exit(2)
    check = ("--check", "") in optlist
    main(check)
