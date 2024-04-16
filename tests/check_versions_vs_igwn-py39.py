"""
This script is a bascic linter that checks that:
  - the versions of the packages in igwn-py39.yaml match those in environment.yml
  - the notebooks don't install anything different from igwn-py39.yaml
    or missing in igwn-py39.yaml

The messages are displayed at the end.
The error code is a combination of the 4 errors:
  - a notebook installs a module that is not in igwn-py39.yaml
  - a notebook installs a different version than igwn-py39.yaml

It requires to download in advance igwn-py39.yaml
"""

import json
import sys
import re
import yaml
from yaml.loader import SafeLoader
import glob


env_file = "../environment.yml"

# Read in the environment yaml file
with open(env_file) as f:
    environment = yaml.load(f, Loader=SafeLoader)



# Extract the dependencies and versions
dependencies = {}
for element in environment["dependencies"]:
    module, version = element.split("=")
    dependencies[module] = version



#check if there is a match between the versions in the environment and in the official igwn file
igwn_file = "../igwn-py39.yaml"
# Read in the igwon yaml file
with open(igwn_file) as f:
    igwn = yaml.load(f, Loader=SafeLoader)
# Extract the dependencies and versions and check that they are the same as the environment

print('\n')
print('Checking consistency between igwn-py39.yaml and environment.yml')
dependencies_igwn = {}
for element in igwn["dependencies"]:
    module, version = element.split("=")[:2]
    dependencies_igwn[module] = version
    if module in dependencies:
        if version != dependencies[module]:
#            raise ValueError(f"Mismatch in versions between environment.yml and igwn-py39.yaml for module {module}: {version} != {dependencies[module]}")
            print(f"Mismatch in versions between igwn-py39.yaml end environment.yml for module {module}: {version} != {dependencies[module]}")
print('Done!')

print('\nChecking consistency between the Tutorials and igwn-py39.yaml ')
files = glob.glob("../Tutorials/Day_*/*ipynb")+ glob.glob("../Tutorials/Extension_topics/*ipynb")

errors = []
for fname in files:
    print(f"Checking {fname}")
    with open(fname, "r") as file:
        content = json.load(file)

    for cell in content["cells"]:
        code = "\n".join(cell["source"])
        if "pip install "in code:
            pip_installs = re.findall("([a-z]+==[0-9\.]+)", code, flags=re.IGNORECASE)
            for element in pip_installs:
                module, version = element.split("==")
                module = module.lower()
                if module in dependencies_igwn:
                    if dependencies_igwn[module] != version:
                        msg = f"Failed: {fname} has a version mismatch in {module}: {version} != {dependencies_igwn[module]}"
                        errors.append(msg)
                    else:
                        msg = f"Passed: {fname} uses {module}: {version}"
                        print(msg)
                else:
                    msg = f"Failed: {fname} needs {module}: {version}, but it is not in the igwn-py39.yaml file"
                    errors.append(msg)

if len(errors) > 0:
    errors = "\n".join(errors)
    msg = f"\nVersion issues: {errors}"
    print(msg)
    sys.exit(1)
