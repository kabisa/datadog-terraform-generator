import argparse
import os
import sys
from os.path import expanduser, join, exists
from typing import Dict

import yaml

HOME = expanduser("~")
CONFIG_DIR = join(HOME, ".datadog_terraform_generator")
CONFIG_FILE = join(CONFIG_DIR, "config.yaml")


def init_config() -> Dict:
    if not exists(CONFIG_DIR):
        os.mkdir(CONFIG_DIR)

    if exists(CONFIG_FILE):
        cont = input(f"Config file {CONFIG_FILE} already exists. Continue? [yN]")
        if cont.strip().upper() != "Y":
            print("goodbye")
            sys.exit()

    config_name = input("Config name:")
    datadog_url = input("Datadog url [https://app.datadoghq.eu/]:")
    if not datadog_url:
        datadog_url = "https://app.datadoghq.eu/"

    api_key = input("Api Key:")
    app_key = input("Application Key:")

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
    store_config(config)


def load_config() -> Dict:
    if not exists(CONFIG_FILE):
        print('First run "ddtfgen init"', file=sys.stderr)
        sys.exit(-1)

    with open(CONFIG_FILE, "r") as fl:
        return yaml.safe_load(fl)


def store_config(config: Dict):
    with open(CONFIG_FILE, "w") as fl:
        yaml.safe_dump(config, fl, indent=2, sort_keys=True)


def switch_context():
    parser = argparse.ArgumentParser()
    parser.add_argument("config_name", help="name of the context you want to switch to")
    args = parser.parse_args()
    config = load_config()
    available_config_names = list(config["configs"])
    if args.config_name not in available_config_names:
        print(
            f"config {args.config_name} does not exist. Available options {','.join(available_config_names)}",
            file=sys.stderr,
        )
        sys.exit()


def get_config_by_name(selected_config_name=None):
    """
    Gets config by name from the config file
    """
    config = load_config()
    selected_config_name = selected_config_name or config["current_config"]
    return config["configs"][selected_config_name]
