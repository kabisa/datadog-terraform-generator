from datadog_terraform_generator.api import DdApi
from datadog_terraform_generator.config_management import get_config_by_name


def get_monitor_by_id(dd_api: DdApi, monitor_id, group_states):
    if group_states is None:
        group_states = ""
    else:
        group_states = f"?group_states={group_states}"
    resp = dd_api.request(f"/api/v1/monitor/{monitor_id}{group_states}")
    print(resp)


def main(args):
    config = get_config_by_name(args.config_name)
    dd_api = DdApi.from_config(config)
    if getattr(args, "monitor_id", None):
        get_monitor_by_id(
            dd_api=dd_api, monitor_id=args.monitor_id, group_states=args.group_states
        )


def add_sub_parser(subparsers):
    parser = subparsers.add_parser("monitors")
    parser.add_argument("--monitor_id")
    parser.add_argument("--group_states")
    parser.set_defaults(func=main)
