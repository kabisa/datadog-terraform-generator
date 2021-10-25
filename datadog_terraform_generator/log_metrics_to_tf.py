from gen_utils import print_hcl, DdApi, get_arg_parser


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


def pull_logs_metrics(dd_api: DdApi, output_file, output_mode="a"):
    data = dd_api.request(path="api/v2/logs/config/metrics")
    with open(output_file, output_mode) as fl:
        for metric in data["data"]:
            tf_code = generate_tf_code(metric_name=metric["id"], **metric["attributes"])
            fl.write(tf_code)

    print(f"Retrieved '{len(data['data'])}' synthetic tests.")


def main():
    parser = get_arg_parser()
    parser.add_argument("--output_file", default="logs_gen.tf")
    parser.add_argument("--output_mode", default="w")
    args = parser.parse_args()

    pull_logs_metrics(
        dd_api=DdApi.from_args(args),
        output_file=args.output_file,
        output_mode=args.output_mode,
    )


if __name__ == "__main__":
    main()
