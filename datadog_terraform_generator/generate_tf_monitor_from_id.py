import re

from datadog_terraform_generator.config_management import get_config_by_name
from datadog_terraform_generator.gen_utils import find_between, canonicalize_tf_name
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


def pull_generic_check(
    dd_api: DdApi, monitor_id, output_dir, monitor_name, param_overrides
):
    data = get_monitor_by_id(dd_api, monitor_id)
    monitor_type = data["type"]
    if monitor_type in ("metric alert", "query alert"):
        return generate_generic_monitor(
            output_dir,
            data,
            monitor_name=monitor_name,
            param_overrides=param_overrides,
        )
    elif monitor_type in ("log alert",):
        return generat_generic_log_monitor(
            output_dir,
            data,
            monitor_name=monitor_name,
            param_overrides=param_overrides,
        )
    else:
        raise NotImplementedError(monitor_type)


def get_monitor_by_id(dd_api, monitor_id) -> dict:
    return dd_api.request(path=f"api/v1/monitor/{monitor_id}")


def monitor_supported(data):
    monitor_type = data["type"]
    if monitor_type in ("metric alert", "query alert", "log alert"):
        return True
    return False


def generat_generic_log_monitor(
    output_dir, data, monitor_name=None, param_overrides=None
):
    name = data["name"]
    if not monitor_supported(data):
        print(f"unsupported monitor type '{data['type']}' in monitor '{name}'")
        return
    (
        alert_message,
        monitor_name,
        critical,
        module_name,
        priority,
        recovery_message,
        service_name_cased,
        warning,
    ) = shared_monitor_settings(monitor_name, data, name)
    query = data["query"]
    m = re.search(r"((\>)|(\>=)|(\<)|(\<=))\s(\d+)$", query)
    # threshold = int(m.group(6))
    operator = m.group(1)
    query_selection_part = query.rsplit(operator)[0].strip()
    query = f"{query_selection_part} {operator} ${{var.MODULE_NAME_critical}}"
    m = re.search(r"\.last\(\"(\w)+\"\)", query)
    evaluation_period = m.group(1)
    query = re.sub(
        r"\.last\(\"(\w)+\"\)", '.last("${var.MODULE_NAME_evaluation_period}")', query
    )
    query = re.sub(r"env:(\w+)", "env:${var.env}", query)

    # escape escape characters
    query = query.replace("\\", "\\\\").replace('"', '\\"')

    vals = determine_vals(
        alert_message,
        monitor_name,
        critical,
        evaluation_period,
        module_name,
        param_overrides,
        priority,
        query,
        recovery_message,
        service_name_cased,
        warning,
    )
    generate(output_dir, **vals)
    return vals


def generate_generic_monitor(output_dir, data, monitor_name=None, param_overrides=None):
    name = data["name"]
    if monitor_name:
        name = monitor_name
    if not monitor_supported(data):
        print(f"unsupported monitor type '{data['type']}' in monitor '{name}'")
        return

    query_parts = data["query"].split(":")
    m = re.search(
        r"(?P<time_agg_fun>\w+)\((?P<evaluation_period>\w+)\)", query_parts[0]
    )
    if not m:
        print(f"Unexpected query {data['query']}")
    time_agg_fun = m.group("time_agg_fun")
    evaluation_period = m.group("evaluation_period")
    query_rest = ":".join(query_parts[2:])
    m = re.search(r"{([^}]+)}", query_rest)
    filter_str = m.group(1)
    (
        alert_message,
        monitor_name,
        critical,
        module_name,
        priority,
        recovery_message,
        service_name_cased,
        warning,
    ) = shared_monitor_settings(monitor_name, data, name)

    loc = get_after_comp_loc(data["query"])
    query = data["query"][: loc + 1] + "${var.MODULE_NAME_critical}"

    query = query.replace(
        f"{time_agg_fun}({evaluation_period})",
        f"{time_agg_fun}(${{var.MODULE_NAME_evaluation_period}})",
    ).replace(filter_str, "${local.MODULE_NAME_filter}")
    vals = determine_vals(
        alert_message,
        monitor_name,
        critical,
        evaluation_period,
        module_name,
        param_overrides,
        priority,
        query,
        recovery_message,
        service_name_cased,
        warning,
    )
    generate(output_dir, **vals)
    return vals, module_name, filter_str


def stringify_val(val) -> str:
    if val is None:
        return "null"
    return str(val)


def determine_vals(
    alert_message,
    monitor_name,
    critical,
    evaluation_period,
    module_name,
    param_overrides,
    priority,
    query,
    recovery_message,
    service_name_cased,
    warning,
):
    vals = load_search_replace_defaults()
    vals.update(
        {
            "module_name": module_name,
            "monitor_name": monitor_name,
            "query": query,
            "alert_message": alert_message,
            "recovery_message": recovery_message,
            "evaluation_period": evaluation_period,
            "critical": stringify_val(critical),
            "warning": stringify_val(warning),
            "priority": stringify_val(priority),
            "service_name": service_name_cased,
        }
    )
    if param_overrides:
        vals.update(param_overrides)
    return vals


def shared_monitor_settings(monitor_name, data, name):
    if "options" not in data:
        raise Exception("Options not found")
    options = data["options"]
    name_parts = name.split("-")
    # Not yet used
    # tags = data["tags"]
    # group_agg_fun = query_parts[1]
    service_name_cased = name_parts[0].strip()
    # locked = options["locked"]
    # require_full_window = options["require_full_window"]
    # new_host_delay = options["new_host_delay"]
    message = data["message"]
    if not monitor_name:
        if "[" in name_parts[-1]:
            monitor_name = name_parts[-2].strip()
        else:
            monitor_name = name_parts[-1].strip()
    module_name = canonicalize_tf_name(monitor_name)
    critical = options["thresholds"]["critical"]
    warning = (
        options["thresholds"]["warning"] if "warning" in options["thresholds"] else None
    )
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
    return (
        alert_message,
        monitor_name,
        critical,
        module_name,
        priority,
        recovery_message,
        service_name_cased,
        warning,
    )


def main(args):
    defaults = load_search_replace_defaults()
    param_overrides = {
        ky: getattr(args, ky, None)
        for ky, default in defaults.items()
        if getattr(args, ky, None) is not None
    }
    config = get_config_by_name(args.config_name)
    pull_generic_check(
        dd_api=DdApi.from_config(config),
        monitor_id=args.monitor_id,
        output_dir=args.output_dir,
        param_overrides=param_overrides,
        monitor_name=args.monitor_name,
    )


def add_sub_parser(subparsers):
    parser = subparsers.add_parser("monitor_from_id")
    parser.add_argument("monitor_id")
    parser.add_argument(
        "output_dir",
        help="directory to generated the files into",
        default=".",
    )
    defaults = load_search_replace_defaults()
    for ky, vl in defaults.items():
        parser.add_argument(f"--{ky}")
    parser.set_defaults(func=main)
