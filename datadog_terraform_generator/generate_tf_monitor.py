#! /usr/bin/env python3
import os
import sys
from os.path import exists

import yaml
from typing import Any, Dict

from datadog_terraform_generator.gen_utils import (
    get_local_abs_path,
    canonicalize_tf_name,
    canonicalize_tf_file_name,
    render_from_template,
)


def generate(output_dir: str, module_name: str, **vals: Dict[str, Any]):
    if canonicalize_tf_name(module_name) != module_name:
        print(
            "Unexpected module name, allowed characters are a-z and _ (underscore) without file extension",
            file=sys.stderr,
        )
        sys.exit()

    # inject module name in vals so we can refer to it during rendering
    vals["module_name"] = module_name

    file_name = canonicalize_tf_file_name(vals["module_name"])
    monitor_path = os.path.normpath(os.path.join(output_dir, file_name))
    variables_path = monitor_path.replace(".tf", "-variables.tf")
    render_from_template("tf-monitor-template.tf", vals, monitor_path)
    render_from_template("tf-monitor-variables-template.tf", vals, variables_path)


def load_search_replace_defaults():
    if exists("tf_monitor_defaults.yaml"):
        defaults_path = "tf_monitor_defaults.yaml"
    else:
        defaults_path = get_local_abs_path("tf_monitor_defaults.yaml")
    with open(defaults_path, "r") as fl:
        return yaml.safe_load(fl)


def main(args):
    defaults = load_search_replace_defaults()
    # get defaults from args
    vals = {ky: getattr(args, ky, default) for ky, default in defaults.items()}
    generate(args.output_dir, args.module_name, **vals)


def add_sub_parser(subparsers):
    parser = subparsers.add_parser("monitor_from_template")
    parser.add_argument(
        "output_dir",
        help="directory to generated the files into",
        default=".",
    )
    parser.add_argument(
        "module_name",
        help="allowed characters are a-z and _ (underscore) without file extension",
    )
    defaults = load_search_replace_defaults()
    for ky, vl in defaults.items():
        parser.add_argument(f"--{ky}", default=vl)
    parser.set_defaults(func=main)
