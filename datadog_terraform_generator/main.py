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
import datadog_terraform_generator.generate_service_file as generate_service_file
import datadog_terraform_generator.query as query
import datadog_terraform_generator.get_terraform_changes as get_terraform_changes
import datadog_terraform_generator.import_generated_module as import_generated_module
import datadog_terraform_generator.downtimes as downtimes
import datadog_terraform_generator.monitors as monitors
import datadog_terraform_generator.list_metric_usage as list_metric_usage
import datadog_terraform_generator.module_versions as module_versions
import datadog_terraform_generator.table as table


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
        generate_service_file.add_sub_parser(sub_parser)
        query.add_sub_parser(sub_parser)
        get_terraform_changes.add_sub_parser(sub_parser)
        import_generated_module.add_sub_parser(sub_parser)
        downtimes.add_sub_parser(sub_parser)
        monitors.add_sub_parser(sub_parser)
        list_metric_usage.add_sub_parser(sub_parser)
        module_versions.add_sub_parser(sub_parser)
        table.add_sub_parser(sub_parser)

    argcomplete.autocomplete(parser)
    args = parser.parse_args()
    args.func(args)
    print("Done")


if __name__ == "__main__":
    sys.argv = [
        "ddtfgen",
        "table",
        "--agg_metric_names",
        "max:rabbitmq.queue.messages",
        "max:rabbitmq.queue.consumers",
        "--group_by",
        "rabbitmq_queue",
        "rabbitmq_vhost",
        "--from",
        "1 hours ago",
        "--to",
        "now",
    ]
    print(" ".join(sys.argv))
    main()
