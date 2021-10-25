import sys

from datadog_terraform_generator.gen_utils import get_arg_parser
import datadog_terraform_generator.generate_tf_monitor as generate_tf_monitor
import datadog_terraform_generator.generate_tf_monitor_from_id as generate_tf_monitor_from_id


def script_found(options_dict):
    for script_name in options_dict:
        if script_name in sys.argv:
            return True
    return False


def main():
    parser = get_arg_parser()
    options_dict = {
        "monitor": generate_tf_monitor.main,
        "monitor_from_id": generate_tf_monitor_from_id.main,
    }
    dont_print_help = script_found(options_dict)
    options = ", ".join(sorted(options_dict))
    parser.add_argument("option", help=f"parser option [{options}]", nargs="+")

    help_option = None
    if dont_print_help:
        new_sys_argv = []
        for arg in sys.argv:
            if arg in ("-h", "--help"):
                help_option = arg
            else:
                new_sys_argv.append(arg)
        sys.argv = new_sys_argv

    args = parser.parse_args()

    main_to_call = options_dict[args.option[0]]
    if help_option:
        new_sys_argv.append(help_option)

    sys.argv = new_sys_argv[1:]
    main_to_call()
    print("Done")
