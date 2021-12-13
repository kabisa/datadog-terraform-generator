from collections import defaultdict

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


def get_metric_list(dd_api: DdApi):
    def get_metric_volume_attribs(metric_name):
        res = dd_api.request(f"api/v2/metrics/{metric_name}/volumes")
        return res["data"]["attributes"]

    get_metric_volume = file_cached(
        func=get_metric_volume_attribs, max_cache_age_seconds=3600 * 24 * 2
    )

    volumes = {}
    prefixes = defaultdict(int)
    total_volume = 0
    try:
        metrics = dd_api.request("api/v2/metrics")
        for metric_def in metrics["data"]:
            metric_name = metric_def["id"]
            volumes[metric_name] = volume = attribs_to_volume(
                get_metric_volume(metric_name)
            )
            parts = metric_name.split(".")
            prefix = parts[0]
            prefixes[prefix] += volume
            total_volume += volume
    except Exception as ex:
        print(ex)

    with open("metric_volume.csv", "w") as fl:
        for key in sorted(volumes, key=lambda k: volumes[k]):
            print(f"{key},{volumes[key]}", file=fl)

    for prefix, volume in prefixes.items():
        print(prefix, str(volume / total_volume * 100)[:5], "%")


def main(args):
    config = get_config_by_name(args.config_name)
    get_metric_list(
        dd_api=DdApi.from_config(config),
    )


def add_sub_parser(subparsers):
    parser = subparsers.add_parser("get_metric_list")
    parser.set_defaults(func=main)


if __name__ == "__main__":
    args = type("args", (object,), {})()
    args.config_name = "tme"
    main(args)
