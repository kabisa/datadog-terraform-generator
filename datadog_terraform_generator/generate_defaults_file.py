import argparse
from os.path import abspath, join

from datadog_terraform_generator.gen_utils import get_local_abs_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "location",
        help="directory where to put the tf_monitor_defaults.yaml file",
        default=".",
    )
    args = parser.parse_args()
    location = abspath(args.location)

    with open(get_local_abs_path("tf_monitor_defaults.yaml"), "r") as fl:
        contents = fl.read()
    with open(join(location, "tf_monitor_defaults.yaml"), "w") as fl:
        fl.write(contents)
