#! /usr/bin/env python3
import os
import yaml
from typing import Any, Dict

from datadog_terraform_generator.gen_utils import get_arg_parser


def fill_template(template: str, vals: Dict[str, Any]) -> str:
    output = template
    for _ in range(100):
        changes_applied = False
        for ky, vl in vals.items():
            ky_upper = ky.upper()
            if ky_upper in output:
                output = output.replace(ky_upper, vl)
                changes_applied = True
        if not changes_applied:
            break
    return output


def get_local_abs_path(file_name):
    return os.path.join(os.path.dirname(__file__), file_name)


def generate(output_dir, **vals: Dict[str, Any]):
    with open(get_local_abs_path("tf-monitor-template.tf"), "r") as mon_template_fl:
        mon_template = mon_template_fl.read()

    with open(
        get_local_abs_path("tf-monitor-variables-template.tf"), "r"
    ) as mon_vars_template_fl:
        mon_vars_template = mon_vars_template_fl.read()

    if os.getcwd().endswith("utils"):
        output_dir = f"../{output_dir}"

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


def load_defaults():
    with open(get_local_abs_path("tf_monitor_defaults.yaml"), "r") as fl:
        return yaml.safe_load(fl)


def main():
    defaults = load_defaults()
    parser = get_arg_parser()
    for ky, vl in defaults.items():
        parser.add_argument(f"--{ky}", default=vl)

    args = parser.parse_args()
    vals = {ky: getattr(args, ky, default) for ky, default in defaults.items()}
    generate(**vals)


if __name__ == "__main__":
    main()
