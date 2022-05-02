import json
import locale
import re
from urllib.parse import urlencode

import arrow
from arrow import Arrow

from datadog_terraform_generator.api import DdApi
from datadog_terraform_generator.config_management import get_config_by_name


def interpret_time(time) -> Arrow:
    if time == "now":
        return arrow.utcnow()
    if "ago" in time:
        cur_locale = locale.getlocale()[0]
        arw = arrow.utcnow()
        return arw.dehumanize(time, cur_locale)
    if re.match(r"\d{10}", time):
        return Arrow.fromtimestamp(int(time))
    return arrow.get(time)


def query(dd_api: DdApi, _from: Arrow, to: Arrow, qry):
    params = {"from": int(_from.timestamp()), "to": int(to.timestamp()), "query": qry}
    return dd_api.request(f"api/v1/query?{urlencode(params)}")


def main(args):
    config = get_config_by_name(args.config_name)
    resp = query(
        dd_api=DdApi.from_config(config),
        _from=interpret_time(getattr(args, "from")),
        to=interpret_time(args.to),
        qry=args.query,
    )
    print(json.dumps(resp))


def add_sub_parser(subparsers):
    parser = subparsers.add_parser(
        "query",
        help="same syntax as in alerts or dashboard widgets, example max:synthetics.http.response.time{*} by {url}",
    )
    parser.add_argument(
        "from", help="Start of the queried time period, seconds since the Unix epoch."
    )
    parser.add_argument(
        "to", help="End of the queried time period, seconds since the Unix epoch."
    )
    parser.add_argument("query", help="Query string")
    parser.set_defaults(func=main)
