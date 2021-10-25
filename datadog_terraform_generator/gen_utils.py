import argparse
import os
from os.path import expanduser, exists, join
from typing import Dict

import requests
import yaml


def find_between(inp, first, last):
    try:
        start = inp.index(first) + len(first)
        end = inp.index(last, start)
        return inp[start:end]
    except ValueError:
        return ""


def print_hcl(mydict, indent=0, quote_keys=False, indent_str="  "):
    """
    Produces a multi-line string for use in terraform tfvars file from a dictionary
    :param mydict: Dict
    :param indent: Should the lines be idented or not
    :return s: Multi-line String in hcl format

    Adapted from: https://github.com/johkerquux/hcl-from-dict/blob/master/printhcl.py
    """

    s = ""
    for key, val in mydict.items():
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


def init_config(config_file_path):
    config_name = input("Config name:")
    datadog_url = input("Datadog url [https://app.datadoghq.eu/]:")
    if not datadog_url:
        datadog_url = "https://app.datadoghq.eu/"

    api_key = input("Api Key")
    app_key = input("Application Key")

    config = {
        "configs": {
            config_name: {
                "datadog_url": datadog_url,
                "api_key": api_key,
                "app_key": app_key,
            }
        },
        "current_config": config_name,
    }
    with open(config_file_path, "w") as fl:
        yaml.safe_dump(config, fl, indent=2, sort_keys=True)


def get_config() -> Dict:
    home = expanduser("~")
    config_dir = join(home, ".datadog_terraform_generator")
    if not exists(config_dir):
        os.mkdir(config_dir)

    config_file = join(config_dir, "config.yaml")
    if not exists(config_file):
        init_config(config_file)

    with open(config_file, "r") as fl:
        return yaml.safe_load(fl)


def get_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    config = get_config()
    parser.add_argument(
        "--current_config",
        help="selects config from ~/.datadog_terraform_generator/config.yaml",
        default=config["current_config"],
    )
    current_config = config["configs"][config["current_config"]]
    parser.add_argument(
        "--api_host",
        help=f"host url of datadog defaults to {current_config['datadog_url']}",
        default=os.environ.get("API_HOST", current_config["datadog_url"]),
    )
    parser.add_argument(
        "--api_key",
        help="datadog api key defaults to env var API_KEY",
        default=os.environ.get("API_KEY", current_config["api_key"]),
    )
    parser.add_argument(
        "--app_key",
        help="datadog application key defaults to env var APP_KEY",
        default=os.environ.get("APP_KEY", current_config["app_key"]),
    )
    return parser


class DdApi:
    def __init__(self, api_host, api_key, app_key):
        self.api_host = api_host
        self.api_key = api_key
        self.app_key = app_key

    def request(self, path):
        url = f"{self.api_host}{path}"
        req = requests.get(
            url,
            headers={
                "DD-API-KEY": self.api_key,
                "DD-APPLICATION-KEY": self.app_key,
                "Content-Type": "application/json",
            },
        )
        req.raise_for_status()
        return req.json()

    @classmethod
    def from_args(cls, args):
        return cls(api_host=args.api_host, api_key=args.api_key, app_key=args.app_key)
