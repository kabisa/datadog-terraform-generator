import re

from datadog_terraform_generator.config_management import get_config_by_name
from datadog_terraform_generator.gen_utils import find_between
from datadog_terraform_generator.api import DdApi
from datadog_terraform_generator.generate_tf_monitor import (
    load_search_replace_defaults,
    generate,
)


def get_after_comp_loc(query):
    for comp in (">", ">=", "<", "<="):
        if comp in query:
            return query.index(comp) + len(comp)
    raise Exception(f"No comparator found in query: {query}")


def pull_generic_check(dd_api: DdApi, monitor_id, output_dir):
    data = dd_api.request(path=f"api/v1/monitor/{monitor_id}")
    query_parts = data["query"].split(":")
    m = re.search(
        r"(?P<time_agg_fun>\w+)\((?P<evaluation_period>\w+)\)", query_parts[0]
    )
    time_agg_fun = m.group("time_agg_fun")
    evaluation_period = m.group("evaluation_period")
    query_rest = ":".join(query_parts[2:])
    options = data["options"]
    name = data["name"]
    name_parts = name.split("-")
    # Not yet used
    # tags = data["tags"]
    # group_agg_fun = query_parts[1]
    # service_name_cased = name_parts[0].strip()
    # locked = options["locked"]
    # require_full_window = options["require_full_window"]
    # new_host_delay = options["new_host_delay"]
    message = data["message"]
    if "[" in name_parts[-1]:
        check_name_cased = name_parts[-2].strip()
    else:
        check_name_cased = name_parts[-1].strip()
    module_name = re.sub(r"[^\w]", "_", check_name_cased).lower()
    m = re.search(r"{([^}]+)}", query_rest)
    filter_str = m.group(1)
    critical = options["thresholds"]["critical"]
    warning = options["thresholds"]["warning"]
    alert_message = (
        "MONITOR_NAME ({{ value }}) in {{ service }} exceeds {{ threshold }}"
    )
    if "{{#is_alert}}" in message:
        alert_message = find_between(message, "{{#is_alert}}", "{{/is_alert}}").strip()

    recovery_message = "MONITOR_NAME ({{ value }}) in {{ service }} has recovered"
    if "{{#is_recovery}}" in message:
        recovery_message = find_between(
            message, "{{#is_recovery}}", "{{/is_recovery}}"
        ).strip()

    priority = data["priority"] or 3

    loc = get_after_comp_loc(data["query"])
    query = data["query"][: loc + 1] + "${var.MODULE_NAME_critical}"

    query = query.replace(
        f"{time_agg_fun}({evaluation_period})",
        f"{time_agg_fun}(${{var.MODULE_NAME_evaluation_period}})",
    ).replace(filter_str, "${local.MODULE_NAME_filter}")
    vals = load_search_replace_defaults()
    vals.update(
        {
            "module_name": module_name,
            "monitor_name": check_name_cased,
            "query": query,
            "alert_message": alert_message,
            "recovery_message": recovery_message,
            "evaluation_period": evaluation_period,
            "critical": str(critical),
            "warning": str(warning),
            "priority": str(priority),
        }
    )
    generate(output_dir, **vals)


def main(args):
    config = get_config_by_name(args.config_name)
    pull_generic_check(
        dd_api=DdApi.from_config(config),
        monitor_id=args.monitor_id,
        output_dir=args.output_dir,
    )


def add_sub_parser(subparsers):
    parser = subparsers.add_parser("monitor_from_id")
    parser.add_argument("monitor_id")
    parser.add_argument(
        "output_dir",
        help="directory to generated the files into",
        default=".",
    )
    parser.set_defaults(func=main)


if __name__ == "__main__":
    main()
