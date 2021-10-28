import argparse
import argcomplete
import sys
from os.path import exists

from datadog_terraform_generator import log_metrics_to_tf
from datadog_terraform_generator.gen_utils import get_arg_parser
import datadog_terraform_generator.generate_tf_monitor as generate_tf_monitor
import datadog_terraform_generator.generate_tf_monitor_from_id as generate_tf_monitor_from_id
import datadog_terraform_generator.generate_defaults_file as generate_defaults_file
import datadog_terraform_generator.generate_tf_module as generate_tf_module
import datadog_terraform_generator.config_management as config_management
import datadog_terraform_generator.mass_state_move as mass_state_move
import datadog_terraform_generator.get_host_list as get_host_list


def script_found(options_dict):
    for script_name in options_dict:
        if script_name in sys.argv:
            return True
    return False


def check_help_options(options_dict):
    """
    We want to make sure the correct script gets to print the help options
    We do some sys.argv tweaking for that
    """
    dont_print_help = script_found(options_dict)
    help_option = None
    new_sys_argv = None
    if dont_print_help:
        new_sys_argv = []
        for arg in sys.argv:
            if arg in ("-h", "--help"):
                help_option = arg
            else:
                new_sys_argv.append(arg)
        sys.argv = new_sys_argv
    return help_option, new_sys_argv


def main():
    config_exists = exists(config_management.CONFIG_FILE)
    parser = get_arg_parser() if config_exists else argparse.ArgumentParser()
    sub_parser = parser.add_subparsers(
        help="subcommand, each subcommand has its own parameters",
    )

    config_management.add_sub_parser(sub_parser, config_exists)
    if config_exists:
        generate_defaults_file.add_sub_parser(sub_parser)
        generate_tf_monitor.add_sub_parser(sub_parser)
        generate_tf_monitor_from_id.add_sub_parser(sub_parser)
        log_metrics_to_tf.add_sub_parser(sub_parser)
        generate_tf_module.add_sub_parser(sub_parser)
        mass_state_move.add_sub_parser(sub_parser)
        get_host_list.add_sub_parser(sub_parser)

    argcomplete.autocomplete(parser)
    args = parser.parse_args()
    args.func(args)
    print("Done")


if __name__ == "__main__":
    sys.argv = [
        "ddtfgen",
        "--config_name",
        "tceu",
        "get_host_list",
        "--host_name_pattern",
        "lxb2c*",
        "--tags_pattern",
        "service:telematics",
    ]
    print(" ".join(sys.argv))
    main()
