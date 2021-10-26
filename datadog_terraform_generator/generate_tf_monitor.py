#! /usr/bin/env python3
import os
from os.path import exists

import yaml
from typing import Any, Dict

from datadog_terraform_generator.gen_utils import (
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
        print(f"Written {monitor_path}")

    with open(variables_path, "w") as mon_vars_fl:
        mon_vars_str = fill_template(mon_vars_template, vals)
        mon_vars_fl.write(mon_vars_str)
        print(f"Written {variables_path}")


def load_search_replace_defaults():
    if exists("tf_monitor_defaults.yaml"):
        defaults_path = "tf_monitor_defaults.yaml"
    else:
        defaults_path = get_local_abs_path("tf_monitor_defaults.yaml")
    with open(defaults_path, "r") as fl:
        return yaml.safe_load(fl)


def main(args):
    defaults = load_search_replace_defaults()
    vals = {ky: getattr(args, ky, default) for ky, default in defaults.items()}
    generate(args.output_dir, **vals)


def add_sub_parser(subparsers):
    parser = subparsers.add_parser("monitor_from_template")
    parser.add_argument(
        "output_dir",
        help="directory to generated the files into",
        default=".",
    )
    defaults = load_search_replace_defaults()
    for ky, vl in defaults.items():
        parser.add_argument(f"--{ky}", default=vl)
    parser.set_defaults(func=main)
