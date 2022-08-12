import json
import os
import shelve
import sys
import time
from typing import List, Optional

from arrow import Arrow

from datadog_terraform_generator.api import DdApi
from datadog_terraform_generator.config_management import get_config_by_name
from datadog_terraform_generator.gen_utils import hash_args_kwargs, CACHE_DIR
from datadog_terraform_generator.query import interpret_time


def list_logs(
    dd_api: DdApi,
    _from: Arrow,
    to: Arrow,
    indexes: List[str],
    query: str,
    cursor: Optional[str] = None,
    limit: int = 1000,
):
    params = {
        "filter": {
            "from": _from.isoformat(),
            "to": to.isoformat(),
            "indexes": indexes,
            "query": query,
        },
        "sort": "timestamp",
        "page": {"limit": limit},
    }
    cache_key = None
    shelve_storage = None

    if cursor is not None:
        params["filter"]["page"]["cursor"] = cursor
        cache_key = hash_args_kwargs(None, params)

    if cache_key:
        cache_path = os.path.join(CACHE_DIR, "list_logs")
        shelve_storage = shelve.open(cache_path)
        if cache_key in shelve_storage:
            return shelve_storage[cache_key]

    result = dd_api.request("api/v2/logs/events/search", data=params)
    if cache_key:
        shelve_storage[cache_key] = result

    return result


def get_paginated_logs(
    dd_api: DdApi,
    _from: Arrow,
    to: Arrow,
    indexes: List[str],
    query: str,
    # cache_name: Optional[str],
    # start_page_token: Optional[str] = None,
):
    resp = list_logs(dd_api=dd_api, _from=_from, to=to, query=query, indexes=indexes)
    yield from resp["data"]
    while resp["meta"]["page"]["after"]:
        resp = list_logs(
            dd_api=dd_api, _from=_from, to=to, query=query, indexes=indexes
        )
        time.sleep(4)
        yield from resp["data"]
    print("done")


def try_get_message(log_item):
    try:
        return log_item["attributes"]["message"]
    except Exception:
        return ""


def main(args):
    config = get_config_by_name(args.config_name)
    if args.output_path == "stdout":
        fl = sys.stdout
    else:
        fl = open(args.output_path, "w")
    cnt = 0

    for item in get_paginated_logs(
        dd_api=DdApi.from_config(config),
        _from=interpret_time(getattr(args, "from")),
        to=interpret_time(args.to),
        query=args.query,
        indexes=args.indexes,
    ):
        if args.output == "csv":
            message = try_get_message(item)
            host = item["attributes"]["host"]
            timestamp = item["attributes"]["timestamp"]
            print(timestamp, host, message.replace("\n", "\t"), file=fl)
        else:
            try:
                print(json.dumps(item["attributes"]["attributes"]), file=fl)
            except Exception as ex:
                print(ex)
        cnt += 1
        if args.limit is not None and args.limit > cnt:
            return
        if args.print_counts and cnt % 100_000 == 0:
            print(cnt)


def add_sub_parser(subparsers):
    parser = subparsers.add_parser("logs")
    parser.add_argument(
        "--from", help="Start of the queried time period, seconds since the Unix epoch."
    )
    parser.add_argument(
        "--to", help="End of the queried time period, seconds since the Unix epoch."
    )
    parser.add_argument("--output", help="Filename to write to", default="stdout")
    parser.set_defaults(func=main)


if __name__ == "__main__":

    class Obj:
        pass

    o = Obj()
    o.config_name = None
    setattr(o, "from", "1 hours ago")
    o.to = "now"
    o.query = "source:kong"
    o.indexes = ["*"]
    o.output = "csv"
    o.output_path = "stdout"
    o.print_counts = True
    o.limit = 5
    main(o)
