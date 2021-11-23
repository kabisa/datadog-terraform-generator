import argparse
import os
import re
import subprocess
import sys
from typing import Dict, Any, List

from argcomplete.completers import ChoicesCompleter

from datadog_terraform_generator.config_management import load_config, list_config_names


def get_local_abs_path(file_name):
    return os.path.join(os.path.dirname(__file__), file_name)


def find_between(inp, first, last):
    try:
        start = inp.index(first) + len(first)
        end = inp.index(last, start)
        return inp[start:end]
    except ValueError:
        return ""


def get_package_file_contents(file_name):
    with open(get_local_abs_path(file_name), "r") as fl:
        return fl.read()


def fill_template(template: str, vals: Dict[str, Any]) -> str:
    """
    Takes a template string and a dict of mappings
    The keys of this dict will be uppercased
    Those uppercased keys wil then be replaced in the template string
    The process stops once no change have been applied for a while
    Note that the replaced value can contain keywords that should be replaced
    That's why we keep trying for a few times
    """
    output = template
    for _ in range(100):
        changes_applied = False
        for ky, vl in vals.items():
            ky_upper = ky.upper()
            if ky_upper in output:
                if vl is None:
                    vl = "null"
                output = output.replace(ky_upper, vl)
                changes_applied = True
        if not changes_applied:
            break
    return output


def render_from_template(
    template_file_name: str, vals: Dict[str, Any], output_file_path: str
):
    mon_template = get_package_file_contents(template_file_name)
    with open(output_file_path, "w") as output_fl:
        contents = fill_template(mon_template, vals)
        output_fl.write(contents)
        print(f"Written {output_file_path}")


def str_fmtr(val) -> str:
    return '"' + str(val.replace('"', '\\"')) + '"'


def print_hcl(input_dict, indent=0, quote_keys=False, indent_str="  "):
    """
    Produces a multi-line string for use in terraform tfvars file from a dictionary
    :param input_dict: Dict
    :param indent: Should the lines be idented or not
    :return s: Multi-line String in hcl format

    Adapted from: https://github.com/johkerquux/hcl-from-dict/blob/master/printhcl.py
    """

    s = ""
    for key, val in input_dict.items():
        s += indent_str * indent
        if isinstance(val, dict):
            use_equal_sign = not key.startswith("_")
            if not use_equal_sign:
                key = key[1:]
            if len(val) > 0:
                fmt_str = "{0} = {1}\n" if use_equal_sign else "{0} {1}\n"
                s += fmt_str.format(
                    key,
                    "{\n"
                    + str(
                        print_hcl(
                            val,
                            indent_str=indent_str,
                            quote_keys=quote_keys,
                            indent=indent + 1,
                        )
                    ).rstrip()
                    + "\n"
                    + indent * indent_str
                    + "}",
                )
        elif isinstance(val, str):
            if indent:
                if quote_keys and key != "value":
                    k = '"{}"'.format(key)
                else:
                    k = key
            else:
                k = key
            s += "{0} = {1}\n".format(k, str_fmtr(val))
        elif isinstance(val, list):
            is_block_list = key.startswith("_")
            if is_block_list:
                key = key[1:]
                for idx, i in enumerate(val):
                    # first key is already indented by beginning of this loop
                    indent_key = idx != 0
                    s += (
                        indent * indent_str * indent_key
                        + key
                        + " {\n"
                        + str(
                            print_hcl(
                                i,
                                indent_str=indent_str,
                                quote_keys=quote_keys,
                                indent=indent + 1,
                            )
                        ).rstrip()
                        + "\n"
                        + indent * indent_str
                        + "}\n"
                    )
                s = s.rstrip()
            else:
                s += key + " = [\n"
                for i in val:
                    s += indent_str * indent
                    if isinstance(i, dict):
                        s += (
                            indent_str * indent
                            + "{"
                            + str(
                                print_hcl(
                                    i,
                                    indent_str=indent_str,
                                    indent=indent + 1,
                                    quote_keys=quote_keys,
                                )
                            ).strip()
                            + "},\n"
                        )
                    else:
                        s += indent_str * indent + '"{}",\n'.format(i)
                s = s[0:-2]
                s += "\n]\n"
        elif val is None:
            if quote_keys:
                s += '"{0}" = {1}\n'.format(key, "null")
            else:
                s += "{0} = {1}\n".format(key, "null")
        else:
            if quote_keys:
                k = '"{}"'.format(key)
            else:
                k = key
            s += "{0} = {1}\n".format(k, str(val).lower())
    return s


def get_arg_parser() -> argparse.ArgumentParser:
    """
    Creates basic argparser that allows to use --config_name
    """
    parser = argparse.ArgumentParser()
    config = load_config()
    parser.add_argument(
        "--config_name",
        help="selects config from ~/.datadog_terraform_generator/config.yaml",
        default=config["current_config"],
    ).completer = ChoicesCompleter(list_config_names())
    return parser


def cli_call(command: List[str], enable_printing=True) -> str:
    if enable_printing:
        print(" ".join(command))
    try:
        output = subprocess.check_output(command)
    except subprocess.CalledProcessError:
        sys.exit()
    output = output.decode("utf-8")
    if enable_printing:
        print(output)
    return output


def input_question(question: str, default_value: str) -> bool:
    assert default_value in ("Y", "N")
    other_val = "n" if default_value == "Y" else "y"
    input_value = input(f"{question} [{default_value}{other_val}]")
    input_value = input_value.strip().upper()
    return input_value == "Y" or (input_value == "" and default_value == "Y")


def canonicalize_tf_name(name: str) -> str:
    return re.sub(r"[\W]", "_", name).lower()


def canonicalize_tf_file_name(name: str) -> str:
    if name.endswith(".tf"):
        name = name[:-3]
    name = re.sub(r"[\W]", "-", name).lower().replace("_", "-")
    while "--" in name:
        name = name.replace("--", "-")
    return f"{name}.tf"
