from os.path import abspath, join

from datadog_terraform_generator.gen_utils import get_local_abs_path


def main(args):
    location = abspath(args.location)

    with open(get_local_abs_path("tf_monitor_defaults.yaml"), "r") as fl:
        contents = fl.read()
    with open(join(location, "tf_monitor_defaults.yaml"), "w") as fl:
        fl.write(contents)


def add_sub_parser(subparsers):
    parser = subparsers.add_parser("defaults_file")
    parser.add_argument(
        "location",
        help="directory where to put the tf_monitor_defaults.yaml file",
        default=".",
    )
    parser.set_defaults(func=main)
