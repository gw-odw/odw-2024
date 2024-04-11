"""
This script is a bascic linter that checks that:
  - the requirements in requirements.txt match those in environment.yml
  - the notebooks don't install anything different from environment.yml
    or missing in environment.yml

The messages are displayed at the end.
The error code is a combination of the 4 errors:
  - requirements.txt installs a module that is not in environment.yml
  - requirements.txt installs a different version than environment.yml
  - a notebook installs a module that is not in environment.yml
  - a notebook installs a different version than environment.yml

TODO:
  - add CLI (for file names, mode of operation, etc.)?
  - should we split that in 2 seperate scripts
    (one for requirements.txt)?
  - extend (or create a new script) to compare environment.yml
    to production environment
"""
import json
import sys
import re
import yaml
from yaml.loader import SafeLoader
import glob


# Error codes and messages
REQ_MISMATCH_ERR = 1 << 0
REQ_MISMATCH_MSG = "Version mismatch in requirements.txt for {module}: requirements.txt requires {version}, environment.yml requires {dependencies_mod}"

REQ_INSTALL_ERR = 1 << 1
REQ_INSTALL_MSG = "Extra installation in requirements.txt: requirements.txt requires {module}=={version}, but it is not in environment.yml"

NB_MISMATCH_ERR = 1 << 2
NB_MISMATCH_MSG = "Version mismatch in {fname} for {module}: notebook requires {version}, environment.yml requires {dependencies_mod}"

NB_INSTALL_ERR = 1 << 3
NB_INSTALL_MSG = "Extra installation in {fname}: this notebook requires {module}=={version}, but it is not in environment.yml"

# Let's be optimistic: there is no error (yet)
errors = []
error_code = 0

env_file = "environment.yml"
requirements_file = "requirements.txt"

# Read in the environment yaml file
with open(env_file) as f:
    environment = yaml.load(f, Loader=SafeLoader)

# Read in the requirements file
requirements = {}
with open(requirements_file) as f:
    for line in f:
        module, version = line.split("==")
        requirements[module] = version.rstrip("\n")


# Extract the dependencies and versions
dependencies = {}
for element in environment["dependencies"]:
    module, version = element.split("=")
    dependencies[module] = version


# Check requirements and dependencies match
# Note requirements.txt is a subset of the full environment.yml
print("Comparing versions in environment.yml and requirements.txt")
for module, version in requirements.items():
    print(f"\tChecking {module}")
    if module in dependencies:
        if version != dependencies[module]:
            # Add message and position error code
            msg = REQ_MISMATCH_MSG.format(
                module=module,
                version=version,
                dependencies_mod=dependencies[module],
            )
            errors.append(msg)
            error_code |= REQ_MISMATCH_ERR
    else:
        # Add message and position error code
        msg = REQ_INSTALL_MSG.format(
            module=module,
            version=version,
        )
        errors.append(msg)
        error_code |= REQ_INSTALL_ERR


print("Checking content of notebooks")
files = glob.glob("Tutorials/Day_*/*ipynb")
for fname in files:
    print(f"\tChecking {fname}")
    with open(fname, "r") as file:
        content = json.load(file)

    for cell in content["cells"]:
        code = "\n".join(cell["source"])
        if "pip install " in code:
            pip_installs = re.findall("([a-z]+==[0-9\.]+)", code)
            for element in pip_installs:
                module, version = element.split("==")
                if module in dependencies:
                    if dependencies[module] != version:
                        # Add message and position error code
                        msg = NB_MISMATCH_MSG.format(
                            fname=fname,
                            module=module,
                            version=version,
                            dependencies_mod=dependencies[module],
                        )
                        errors.append(msg)
                        error_code |= NB_MISMATCH_ERR
                else:
                    # Add message and position error code
                    msg = NB_INSTALL_MSG.format(
                        fname=fname,
                        module=module,
                        version=version,
                    )
                    errors.append(msg)
                    error_code |= NB_INSTALL_ERR

if errors:
    print("Error(s) found:")
    print("\n".join(errors))
    sys.exit(error_code)
