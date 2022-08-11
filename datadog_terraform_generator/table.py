import csv
import locale
import math
import sys
from typing import Dict, List

from datadog_terraform_generator.api import DdApi
from datadog_terraform_generator.config_management import get_config_by_name
from datadog_terraform_generator.query import query, interpret_time


def table(
    agg_metric_names: List[str],
    group_by: List[str],
    _from: str,
    to: str,
    output_path: str,
):

    locale.setlocale(category=locale.LC_CTYPE, locale="en_us")
    config = get_config_by_name(None)
    dd_api = DdApi.from_config(config)
    from_arrow = interpret_time(_from)
    to_arrow = interpret_time(to)
    filter_str = "*"
    if group_by:
        group_by_str = " by {" + ",".join(group_by) + "}"
    else:
        group_by_str = ""

    metric_aggregations, metric_data = query_metrics(
        agg_metric_names=agg_metric_names,
        dd_api=dd_api,
        filter_str=filter_str,
        group_by_str=group_by_str,
        from_arrow=from_arrow,
        to_arrow=to_arrow,
    )

    rows = metric_data_to_rows(metric_data, metric_aggregations)

    if output_path == "stdout":
        fl = sys.stdout
    else:
        fl = open(output_path, "w")
    writer = csv.writer(fl)
    writer.writerows(rows)


def query_metrics(
    agg_metric_names, dd_api, filter_str, group_by_str, from_arrow, to_arrow
):
    metric_data = {}
    metric_aggregations = {}
    for agg_metric in agg_metric_names:
        aggregation, metric_name = agg_metric.split(":", maxsplit=1)
        assert aggregation == "max", "our aggregation code only understands max for now"
        metric_aggregations[metric_name] = aggregation
        query_res = query(
            _from=from_arrow,
            to=to_arrow,
            qry=f"{aggregation}:{metric_name}{{{filter_str}}}{group_by_str}",
            dd_api=dd_api,
        )

        query_res_to_metric_data(query_res, metric_data)
    return metric_aggregations, metric_data


def metric_data_to_rows(
    metric_data: Dict[str, Dict], metric_aggregations: Dict[str, str]
) -> List[List]:
    headers_written = False
    headers = ["tagset"]
    output_list = [headers]
    for ky in sorted(metric_data):
        metrics = metric_data[ky]
        item = [ky]
        output_list.append(item)
        for metric_name in sorted(metrics):
            if not headers_written:
                headers.append(f"{metric_aggregations[metric_name]}({metric_name})")
            item.append(metrics[metric_name])
        headers_written = True
    return output_list


def query_res_to_metric_data(query_res, metric_data: Dict):
    for item in query_res["series"]:
        tagset_str = ",".join(item["tag_set"])
        cur_metric = item["metric"]

        if tagset_str not in metric_data:
            metric_data[tagset_str] = {}
        if cur_metric not in metric_data[tagset_str]:
            metric_data[tagset_str][cur_metric] = -math.inf
        for point in item["pointlist"]:
            if point[1] is None:
                continue
            if point[1] > metric_data[tagset_str][cur_metric]:
                metric_data[tagset_str][cur_metric] = point[1]


def main(args):
    table(
        agg_metric_names=[
            "max:rabbitmq.queue.messages",
            "max:rabbitmq.queue.consumers",
        ],
        _from=getattr(args, "from"),
        to=args.to,
        group_by=args.group_by,
        output_path=args.output,
    )


def add_sub_parser(subparsers):
    parser = subparsers.add_parser("table")
    parser.add_argument(
        "--agg_metric_names",
        nargs="+",
        help="Metric names and their aggregations. This is your columns. Example: agg_metric_names agg:metric.name agg:metric.name2",
    )
    parser.add_argument(
        "--group_by",
        nargs="+",
        help="Group By. This is your rows. Example: agg_metric_names agg:metric.name agg:metric.name2",
    )
    parser.add_argument(
        "--from", help="Start of the queried time period, seconds since the Unix epoch."
    )
    parser.add_argument(
        "--to", help="End of the queried time period, seconds since the Unix epoch."
    )
    parser.add_argument("--output", help="Filename to write to", default="stdout")
    parser.set_defaults(func=main)


if __name__ == "__main__":
    table(
        agg_metric_names=[
            "max:rabbitmq.queue.messages",
            "max:rabbitmq.queue.consumers",
        ],
        _from="1 hours ago",
        to="now",
        group_by=["rabbitmq_queue", "rabbitmq_vhost", "cloudamqp-name"],
        output_path="tmp.csv",
    )
