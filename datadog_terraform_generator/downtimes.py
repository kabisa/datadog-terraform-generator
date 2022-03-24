from datadog_terraform_generator.api import DdApi
from datadog_terraform_generator.config_management import get_config_by_name


def get_active_downtimes(dd_api: DdApi, current_only: bool):
    resp = dd_api.request(f"/api/v1/downtime?current_only={bool(current_only)}")
    print(resp)


def get_downtime_by_id(dd_api: DdApi, downtime_id):
    resp = dd_api.request(f"/api/v1/downtime/{downtime_id}")
    print(resp)


def main(args):
    config = get_config_by_name(args.config_name)
    dd_api = DdApi.from_config(config)
    if getattr(args, "downtime_id", None):
        get_downtime_by_id(dd_api=dd_api, downtime_id=args.downtime_id)
    else:
        get_active_downtimes(dd_api=dd_api, current_only=args.current_only)


def add_sub_parser(subparsers):
    parser = subparsers.add_parser("downtimes")
    parser.add_argument(
        "--current_only",
        help="Only return downtimes that are active when the request is made.",
        action="store_true",
    )
    parser.add_argument("--downtime_id")
    parser.set_defaults(func=main)
