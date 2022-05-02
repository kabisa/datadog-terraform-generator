import time
from collections import defaultdict
from typing import Optional

from datadog_terraform_generator.api import DdApi
from datadog_terraform_generator.config_management import get_config_by_name
from datadog_terraform_generator.gen_utils import file_cached


def attribs_to_volume(attribs):
    # Not sure about the correctness of this one
    return (
        attribs.get("distinct_volume")
        or attribs.get("metric_volume")
        or attribs.get("ingested_volume")
    )


def get_metric_list(
    dd_api: DdApi,
    metric_name_prefix_filter: Optional[str],
    sleep_time=3.4,
    split_char=".",
):
    def get_metric_volume_attribs(metric_name):
        print(metric_name)
        # Default rate for this is 3 requests in 10 secs
        # https://docs.datadoghq.com/api/latest/rate-limits/
        time.sleep(sleep_time)
        res = dd_api.request(f"api/v2/metrics/{metric_name}/volumes")
        return res["data"]["attributes"]
        # return "skip"

    get_metric_volume = file_cached(
        func=get_metric_volume_attribs, max_cache_age_seconds=3600 * 24 * 1
    )

    prefix_filter_len = (
        len(metric_name_prefix_filter) if metric_name_prefix_filter else 0
    )
    volumes = {}
    prefixes = defaultdict(int)
    total_volume = 0
    try:
        metrics = dd_api.request("api/v2/metrics")
        for metric_def in metrics["data"]:
            metric_name = metric_def["id"]
            if metric_name_prefix_filter and not metric_name.startswith(
                metric_name_prefix_filter
            ):
                continue
            attribs = get_metric_volume(metric_name)
            if attribs == "skip":
                continue
            volume = attribs_to_volume(attribs)
            if volume is None:
                continue
            volumes[metric_name] = volume
            parts = metric_name[prefix_filter_len:].lstrip(split_char).split(split_char)
            prefix = parts[0]
            prefixes[prefix] += volume
            total_volume += volume
    except Exception as ex:
        print(ex)

    with open("metric_volume.csv", "w") as fl:
        for key in sorted(volumes, key=lambda k: volumes[k]):
            if metric_name_prefix_filter and not key.startswith(
                metric_name_prefix_filter
            ):
                continue
            print(f"{key},{volumes[key]}", file=fl)

    for prefix, volume in prefixes.items():
        print(
            metric_name_prefix_filter + prefix,
            str(volume / total_volume * 100)[:5],
            "%",
        )


def main(args):
    config = get_config_by_name(args.config_name)
    get_metric_list(
        dd_api=DdApi.from_config(config),
        metric_name_prefix_filter=getattr(args, "prefix", ""),
    )


def add_sub_parser(subparsers):
    parser = subparsers.add_parser("get_metric_list")
    parser.add_argument(
        "--prefix", help="supply a prefix, only get the metric usage for that prefix"
    )
    parser.set_defaults(func=main)


if __name__ == "__main__":
    args = type("args", (object,), {})()
    args.config_name = "tme"
    args.prefix = "digazu"
    main(args)
