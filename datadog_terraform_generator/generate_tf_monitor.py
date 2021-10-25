#! /usr/bin/env python3
import os
from os.path import exists

import yaml
from typing import Any, Dict

from datadog_terraform_generator.gen_utils import (
    get_arg_parser,
    get_local_abs_path,
    get_package_file_contents,
    fill_template,
)


def generate(output_dir, **vals: Dict[str, Any]):
    mon_template = get_package_file_contents("tf-monitor-template.tf")
    mon_vars_template = get_package_file_contents("tf-monitor-variables-template.tf")

    file_name = vals["module_name"].replace("_", "-") + ".tf"
    while "--" in file_name:
        file_name = file_name.replace("--", "-")

    monitor_path = os.path.normpath(os.path.join(output_dir, file_name))
    variables_path = monitor_path.replace(".tf", "-variables.tf")

    with open(monitor_path, "w") as monitor_fl:
        monitor_str = fill_template(mon_template, vals)
        monitor_fl.write(monitor_str)

    with open(variables_path, "w") as mon_vars_fl:
        mon_vars_str = fill_template(mon_vars_template, vals)
        mon_vars_fl.write(mon_vars_str)


def load_search_replace_defaults():
    if exists("tf_monitor_defaults.yaml"):
        defaults_path = "tf_monitor_defaults.yaml"
    else:
        defaults_path = get_local_abs_path("tf_monitor_defaults.yaml")
    with open(defaults_path, "r") as fl:
        return yaml.safe_load(fl)


def main():
    defaults = load_search_replace_defaults()
    parser = get_arg_parser()
    for ky, vl in defaults.items():
        parser.add_argument(f"--{ky}", default=vl)

    args = parser.parse_args()
    vals = {ky: getattr(args, ky, default) for ky, default in defaults.items()}
    generate(**vals)


if __name__ == "__main__":
    main()
