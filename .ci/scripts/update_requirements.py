import getopt
import re
import sys
import typing as t
from pathlib import Path

from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.version import Version


def fix_requirements_file(path: Path, check: bool, specs: t.Dict[str, SpecifierSet]) -> None:
    changed = False
    lines = path.read_text().split("\n")
    for name, specifier in specs.items():
        for num, line in enumerate(lines):
            try:
                requirement = Requirement(line)
            except Exception:
                # Ignore unparsable lines.
                continue
            if requirement.name == name:
                if requirement.specifier == specifier:
                    break
                elif check:
                    print(f"{path} has unmatched {name} requirement.")
                    sys.exit(1)
                else:
                    print(f"Update {path}.")
                    requirement.specifier = specifier
                    lines[num] = str(requirement)
                    changed = True
                    break
        else:
            print(f"{name} requirement missing from {path}.")
            sys.exit(1)

    if changed:
        path.write_text("\n".join(lines))
    else:
        print(f"{path} is up to date.")


def main(check: bool) -> None:
    pulp_glue_path = Path("plugins/module_utils/pulp_glue.py")
    requirements_path = Path("requirements-test.txt")
    lower_bounds_path = Path("lower_bounds_constraints.lock")

    version_spec_regex = {
        "pulp-glue": re.compile(r"^\s*GLUE_VERSION_SPEC\s*=\s*\"(.*)\"$"),
        "pulp-glue-deb": re.compile(r"^\s*GLUE_DEB_VERSION_SPEC\s*=\s*\"(.*)\"$"),
    }
    version_specs: t.Dict[str, SpecifierSet] = {}
    lower_bounds_specs: t.Dict[str, SpecifierSet] = {}

    with pulp_glue_path.open("r") as fp:
        for line in fp.readlines():
            for name, regex in version_spec_regex.items():
                if match := re.search(regex, line):
                    version_spec = SpecifierSet(match.group(1))
                    version_spec_regex.pop(name)
                    version_specs[name] = version_spec

                    try:
                        min_version = min(
                            [
                                Version(spec.version)
                                for spec in version_spec
                                if spec.operator == ">="
                            ]
                        )
                        lower_bounds_specs[name] = SpecifierSet(f"=={min_version}")
                    except ValueError:
                        print("No lower bound requirement specified for pulp-glue.")
                        sys.exit(1)

                    break
            if not version_spec_regex:
                # We found them all.
                break
        else:
            keys = ", ".join(version_spec_regex.keys())
            print(f"Specs for {keys} not found!")
            sys.exit(1)

    fix_requirements_file(requirements_path, check, version_specs)
    fix_requirements_file(lower_bounds_path, check, lower_bounds_specs)


if __name__ == "__main__":
    optlist, args = getopt.getopt(sys.argv[1:], "", ["check"])
    if args:
        print("Too many arguments!")
        sys.exit(2)
    check = ("--check", "") in optlist
    main(check)
