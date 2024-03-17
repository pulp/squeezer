import re
import sys
from pathlib import Path

from packaging.requirements import Requirement
from packaging.specifiers import Specifier, SpecifierSet
from packaging.version import Version


def fix_requirements_file(path: Path, check: bool, name: str, specifier: SpecifierSet) -> None:
    lines = path.read_text().split("\n")
    for num, line in enumerate(lines):
        try:
            requirement = Requirement(line)
        except:
            pass
        else:
            if requirement.name == name:
                if requirement.specifier == specifier:
                    print(f"{path} is up to date.")
                    break
                elif check:
                    print(f"{path} has unmatched pulp-glue requirement.")
                    sys.exit(1)
                else:
                    print(f"Update {path}.")
                    requirement.specifier = specifier
                    lines[num] = str(requirement)
                    path.write_text("\n".join(lines))
                    break
    else:
        print(f"{name} requirement missing from {path}.")
        sys.exit(1)


def main(check: bool) -> None:
    pulp_glue_path = Path("plugins/module_utils/pulp_glue.py")
    requirements_path = Path("requirements.txt")
    lower_bounds_path = Path("lower_bounds_constraints.lock")

    with pulp_glue_path.open("r") as fp:
        for line in fp.readlines():
            if match := re.search(r"GLUE_VERSION_SPEC\s*=\s*\"(.*)\"", line):
                GLUE_VERSION_SPEC = SpecifierSet(match.group(1))
                break
        else:
            print("GLUE_VERSION_SPEC not found!")
            sys.exit(1)
    try:
        min_version = min(
            [Version(spec.version) for spec in GLUE_VERSION_SPEC if spec.operator == ">="]
        )
    except ValueError:
        print("No lower bound requirement specified for pulp-glue.")
        sys.exit(1)
    lower_bounds_spec = Specifier(f"=={min_version}")

    fix_requirements_file(requirements_path, check, "pulp-glue", GLUE_VERSION_SPEC)
    fix_requirements_file(lower_bounds_path, check, "pulp-glue", lower_bounds_spec)


if __name__ == "__main__":
    check = len(sys.argv) == 2 and sys.argv[1] == "--check"
    main(check)
