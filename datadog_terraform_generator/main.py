import argparse
import sys
from os.path import exists

from datadog_terraform_generator import log_metrics_to_tf
from datadog_terraform_generator.config_management import (
    CONFIG_FILE,
    init_config,
    switch_context,
)
from datadog_terraform_generator.gen_utils import get_arg_parser
import datadog_terraform_generator.generate_tf_monitor as generate_tf_monitor
import datadog_terraform_generator.generate_tf_monitor_from_id as generate_tf_monitor_from_id
import datadog_terraform_generator.generate_defaults_file as generate_defaults_file


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
    options_dict = {
        "init": init_config,
    }

    if exists(CONFIG_FILE):
        parser = get_arg_parser()
        options_dict.update(
            {
                "monitor_from_template": generate_tf_monitor.main,
                "monitor_from_id": generate_tf_monitor_from_id.main,
                "log_metrics": log_metrics_to_tf.main,
                "defaults": generate_defaults_file.main,
                "switch_context": switch_context,
            }
        )
    else:
        parser = argparse.ArgumentParser()

    options = ", ".join(sorted(options_dict))
    parser.add_argument("option", help=f"parser option [{options}]", nargs="+")
    help_option, new_sys_argv = check_help_options(options_dict)
    args = parser.parse_args()

    main_to_call = options_dict[args.option[0]]
    if help_option:
        new_sys_argv.append(help_option)

    sys.argv = new_sys_argv[1:]
    main_to_call()
    print("Done")
