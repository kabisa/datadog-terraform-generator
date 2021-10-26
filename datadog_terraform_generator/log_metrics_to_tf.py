from datadog_terraform_generator.config_management import get_config_by_name
from datadog_terraform_generator.gen_utils import print_hcl, get_arg_parser
from datadog_terraform_generator.api import DdApi


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


def pull_logs_metrics(dd_api: DdApi, output_file, metric_name, output_mode="a"):
    data = dd_api.request(path="api/v2/logs/config/metrics")
    lookup = {}
    for metric in data["data"]:
        if metric_name == "all" or metric["id"] == metric_name:
            lookup[metric["id"]] = metric

    with open(output_file, output_mode) as fl:
        for ky in sorted(lookup):
            metric = lookup[ky]
            tf_code = generate_tf_code(metric_name=metric["id"], **metric["attributes"])
            fl.write(tf_code)

    metrics_listed = "\n- ".join(sorted(lookup))
    print(f"Retrieved {len(lookup)} log metrics: \n{metrics_listed}")


def main():
    parser = get_arg_parser()
    parser.add_argument(
        "metric_name",
        help="Give the metric name you want to pull, [all] is also an option",
    )
    parser.add_argument("output_file", help="Filename to output the terraform code to")
    parser.add_argument(
        "--output_mode",
        help="w for [w]rite to file, a for [a]ppend to file",
        default="w",
    )
    args = parser.parse_args()
    config = get_config_by_name(args.config_name)
    pull_logs_metrics(
        dd_api=DdApi.from_config(config),
        output_file=args.output_file,
        output_mode=args.output_mode,
        metric_name=args.metric_name,
    )


if __name__ == "__main__":
    main()
