from fnmatch import fnmatch

from datadog_terraform_generator.config_management import get_config_by_name
from datadog_terraform_generator.gen_utils import print_hcl, cli_call
from datadog_terraform_generator.api import DdApi
from datadog_terraform_generator.terraform_calls import get_state_list

TF_TEMPLATE = """
resource "datadog_logs_metric" "{metric_underscored}" {{
{content}
}}
"""


def generate_tf_code(metric_name, filter, compute, **optionals):
    """
    Generate terraform code for: datadog_logs_metric
    Filter and Compute are required
    """
    return TF_TEMPLATE.format(
        metric_name=metric_name,
        metric_underscored=metric_name.replace(".", "_"),
        content=print_hcl(
            {
                "name": metric_name,
                "_compute": compute,
                "_filter": filter,
                **{f"_{ky}": vl for ky, vl in optionals.items()},
            },
            indent=True,
        ),
    )


def pull_logs_metrics(
    dd_api: DdApi, output_file, metric_name, output_mode="a", import_prefix=None
):
    data = dd_api.request(path="api/v2/logs/config/metrics")
    lookup = {}
    for metric in data["data"]:
        if metric_name == "all" or fnmatch(metric["id"], metric_name):
            lookup[metric["id"]] = metric

    metrics_listed = "\n - ".join(sorted(lookup))
    print(f"Retrieved {len(lookup)} log metrics: \n - {metrics_listed}")

    with open(output_file, output_mode) as fl:
        for ky in sorted(lookup):
            metric = lookup[ky]
            tf_code = generate_tf_code(metric_name=metric["id"], **metric["attributes"])
            fl.write(tf_code)
        print(f"Written {output_file}")

    if import_prefix:
        if not import_prefix.endswith("."):
            import_prefix += "."
        if not import_prefix.endswith("datadog_logs_metric."):
            import_prefix += "datadog_logs_metric."

        state_list = get_state_list()
        for ky in sorted(lookup):
            metric = lookup[ky]
            metric_name = metric["id"]
            metric_name_underscored = metric_name.replace(".", "_")
            import_path = f"{import_prefix}{metric_name_underscored}"
            if import_path in state_list:
                print(f"skipping import {import_path}")
                continue
            cli_call(["terraform", "import", import_path, metric_name])


def main(args):
    config = get_config_by_name(args.config_name)
    pull_logs_metrics(
        dd_api=DdApi.from_config(config),
        output_file=args.output_file,
        output_mode=args.output_mode,
        metric_name=args.metric_name_pattern,
        import_prefix=args.import_prefix,
    )


def add_sub_parser(subparsers):
    parser = subparsers.add_parser("log_metrics")
    parser.add_argument(
        "metric_name_pattern",
        help="""Give the pattern with whitch the metric needs to match
             Patterns are Unix shell style:
             *       matches everything
             ?       matches any single character
             [seq]   matches any character in seq
             [!seq]  matches any char not in seq
             """,
    )
    parser.add_argument("output_file", help="Filename to output the terraform code to")
    parser.add_argument(
        "--output_mode",
        help="w for [w]rite to file, a for [a]ppend to file",
        default="w",
    )
    parser.add_argument(
        "--import_prefix",
        help="this will trigger terraform imports to be executed as well",
        default=None,
    )
    parser.set_defaults(func=main)
