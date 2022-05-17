import sys
import csv

from urllib.parse import urlencode

from datadog_terraform_generator.api import DdApi
from datadog_terraform_generator.config_management import get_config_by_name


def get_monitor_by_id(dd_api: DdApi, monitor_id, group_states):
    if group_states is None:
        group_states = ""
    else:
        group_states = f"?group_states={group_states}"
    resp = dd_api.request(f"api/v1/monitor/{monitor_id}{group_states}")
    print(resp)


def format_notification_channel(notification_channel_dict: dict) -> str:
    return notification_channel_dict["handle"]


def pages_left(metadata) -> bool:
    return metadata["page"] < metadata["page_count"]


def get_monitors_by_query(dd_api: DdApi, query: str):
    resp = None
    params = {"query": query, "page": 0}
    writer = csv.writer(
        sys.stdout, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL
    )
    writer.writerow(
        [
            "id",
            "name",
            "tags",
            "notifications",
            "query",
        ]
    )
    count = 0
    while resp is None or pages_left(resp["metadata"]):
        formatted_qry = urlencode(params)
        resp = dd_api.request(f"api/v1/monitor/search?{formatted_qry}")
        for monitor in resp["monitors"]:
            writer.writerow(
                [
                    str(monitor["id"]),
                    monitor["name"],
                    ",".join(monitor["tags"]),
                    ",".join(
                        format_notification_channel(chan)
                        for chan in monitor["notifications"]
                    ),
                    monitor["query"].replace("\\", "\\\\").replace('"', '"'),
                ]
            )
            count += 1
        params["page"] += 1
    print("Count:", count)


def main(args):
    config = get_config_by_name(args.config_name)
    dd_api = DdApi.from_config(config)
    if getattr(args, "monitor_id", None):
        get_monitor_by_id(
            dd_api=dd_api, monitor_id=args.monitor_id, group_states=args.group_states
        )
    elif getattr(args, "query", None):
        get_monitors_by_query(dd_api=dd_api, query=args.query)
    else:
        raise NotImplementedError("Parameters unset?")


def add_sub_parser(subparsers):
    parser = subparsers.add_parser("monitors")
    parser.add_argument("--monitor_id")
    parser.add_argument("--query")
    parser.add_argument("--group_states")
    parser.set_defaults(func=main)


if __name__ == "__main__":

    class Object:
        pass

    args = Object()
    args.query = 'service:"kong" notification:servicenow-toyotaeurope'
    args.config_name = ""
    main(args)
