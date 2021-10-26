import os
import sys
from os.path import join, isdir, isfile, dirname, abspath

from urllib.parse import urlencode

from datadog_terraform_generator.api import DdApi
from datadog_terraform_generator.config_management import get_config_by_name
from datadog_terraform_generator.generate_tf_monitor_from_id import (
    generate_generic_monitor,
    monitor_supported,
    get_monitor_by_id,
)


from datadog_terraform_generator.gen_utils import (
    get_package_file_contents,
    fill_template,
    str_fmtr,
)


def write_module_file(module_path, file_name, contents, replacements):
    replaced_contents = fill_template(contents, replacements)
    file_path = join(module_path, file_name)
    with open(file_path, "w") as fl:
        fl.write(replaced_contents)
        print(f"Written {file_path}")


def generate_module(module_path, service_name, min_provider_version):
    replacements = {
        "MIN_PROVIDER_VERSION": min_provider_version,
        "SERVICE_NAME": str_fmtr(service_name)
        if isinstance(service_name, str)
        else "null",
    }
    files = [
        ("tf-module-provider.tf", "provider.tf"),
        ("tf-module-variables.tf", "variables.tf"),
    ]
    for packaged_file, output_file in files:
        tf = get_package_file_contents(packaged_file)
        write_module_file(module_path, output_file, tf, replacements)

    # empty main.tf
    write_module_file(module_path, "main.tf", "\n", {})


def main(args):
    if isfile(args.module_path):
        print(f"Module path is a file {args.module_path}, exiting", file=sys.stderr)
        sys.exit()

    if not isdir(dirname(abspath(args.module_path))):
        print(
            f"Module path: '{args.module_path}', parent directory does not exist '{dirname(args.module_path)}'",
            file=sys.stderr,
        )
        sys.exit()

    if not isdir(args.module_path):
        create_dir = input("module directory does not exist yet, create? [Yn]")
        if create_dir.upper() == "Y" or len(create_dir) == 0:
            os.mkdir(args.module_path)
        else:
            print("Ok exiting")
            sys.exit()

    service_name = None
    if args.from_query:
        config = get_config_by_name(args.config_name)
        dd_api = DdApi.from_config(config)
        params = {"query": args.from_query}
        data = dd_api.request(f"api/v1/monitor/search?{urlencode(params)}")
        for monitor in data["monitors"]:
            if not monitor_supported(monitor):
                print(
                    f"unsupported monitor type '{monitor['type']}' in monitor '{monitor['name']}'"
                )
                continue

            monitor = get_monitor_by_id(dd_api, monitor["id"])
            monitor_vals = generate_generic_monitor(
                output_dir=args.module_path, data=monitor
            )
            if monitor_vals:
                service_name = monitor_vals.get("service_name", service_name)

    use_svc_name = input(
        f"I've found the following service name: {service_name} do you want to use it? [Yn]"
    )
    if use_svc_name.upper() != "Y" and use_svc_name:
        service_name = args.service_name

    generate_module(
        module_path=args.module_path,
        service_name=service_name,
        min_provider_version=args.provider_version,
    )


def add_sub_parser(subparsers):
    parser = subparsers.add_parser("module")
    parser.add_argument(
        "module_path", help="The full path of the module eg ./modules/mymodule"
    )
    parser.add_argument("--service_name", help="Name of the service", default=None)
    parser.add_argument(
        "--provider_version", help="Minimal version of datadog provider", default="2.21"
    )
    parser.add_argument(
        "--from_query",
        help="provide a query string like you would in the datadog UI to search for monitors. All results will be added in the new module",
        default=None,
    )
    parser.set_defaults(func=main)
