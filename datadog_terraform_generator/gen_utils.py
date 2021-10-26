import argparse
import os
from typing import Dict, Any


from datadog_terraform_generator.config_management import load_config


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
                output = output.replace(ky_upper, vl)
                changes_applied = True
        if not changes_applied:
            break
    return output


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
            s += "{0} = {1}\n".format(k, '"' + str(val.replace('"', '\\"')) + '"')
        elif isinstance(val, list):
            is_block_list = key.startswith("_")
            if is_block_list:
                key = key[1:]
                for i in val:
                    s += (
                        key
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
            if indent:
                s += '"{0}" = {1}\n'.format(key, '""')
            else:
                s += "{0} = {1}\n".format(key, '""')
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
    )
    return parser
