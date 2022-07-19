import os
import sys
from os.path import join, isdir, isfile, dirname, abspath

from urllib.parse import urlencode

from datadog_terraform_generator.api import DdApi
from datadog_terraform_generator.config_management import get_config_by_name
from datadog_terraform_generator.generate_tf_monitor import load_search_replace_defaults
from datadog_terraform_generator.generate_tf_monitor_from_id import (
    generate_generic_monitor,
    monitor_supported,
    get_monitor_by_id,
)
from datadog_terraform_generator.gen_utils import (
    get_package_file_contents,
    fill_template,
    str_fmtr,
    input_question,
    canonicalize_tf_name,
    canonicalize_tf_file_name,
    render_from_template,
)
from datadog_terraform_generator.terraform_calls import terraform_import, terraform_init


IMPORT_SUGGESTIONS_FILE_NAME = "terraform_import_suggestions.txt"


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


def generate_modules_from_query(args, service_name, param_overrides):
    tf_imports = []
    filter_strings = set([])
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
        monitor_vals, module_name, filter_str = generate_generic_monitor(
            output_dir=args.module_path, data=monitor, param_overrides=param_overrides
        )
        filter_strings.add(filter_str)
        if monitor_vals and not service_name:
            service_name = monitor_vals.get("service_name")
        if module_name:
            tf_imports.append(
                (
                    f"module.{module_name}.datadog_monitor.generic_datadog_monitor[0]",
                    f"{monitor['id']}",
                )
            )
    if tf_imports:
        with open(
            os.path.join(args.module_path, IMPORT_SUGGESTIONS_FILE_NAME), "w"
        ) as fl:
            fl.write(
                "\n".join(
                    [
                        f"{item_path};{monitor_id}"
                        for item_path, monitor_id in tf_imports
                    ]
                )
            )
    return service_name, tf_imports, filter_strings


def make_sure_module_dir(args):
    if not isdir(args.module_path):
        if input_question(
            "module directory does not exist yet, create?", default_value="Y"
        ):
            os.mkdir(args.module_path)
        else:
            print("Ok exiting")
            sys.exit()


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

    make_sure_module_dir(args)
    service_name = args.service_name
    tf_imports = None
    filter_strings = None
    if args.from_query:
        defaults = load_search_replace_defaults()
        param_overrides = {
            ky: getattr(args, ky, None)
            for ky, default in defaults.items()
            if getattr(args, ky, None) is not None
        }
        service_name, tf_imports, filter_strings = generate_modules_from_query(
            args, service_name, param_overrides
        )

    if args.service_name is None and service_name is not None:
        use_svc_name = input_question(
            f"I've found the following service name: {service_name} do you want to use it?",
            default_value="Y",
        )
        if not use_svc_name:
            service_name = None

    filter_str = None
    generate_module_usage = input_question("generate module usage?", default_value="Y")
    if generate_module_usage:
        if not service_name:
            service_name = input("Service name:")
        service_name_canonicalized = canonicalize_tf_name(service_name)
        importing_module_name = input(f"Module name [{service_name_canonicalized}]:")
        if not importing_module_name:
            importing_module_name = service_name
        importing_module_name = canonicalize_tf_name(importing_module_name)
        importing_module_file_name = canonicalize_tf_file_name(importing_module_name)
        if filter_strings:
            filter_str_list = list(filter_strings)
            filter_str_options = "\n".join(
                f"[{idx}] {filter_str}"
                for idx, filter_str in enumerate(filter_str_list)
            )
            response = input(
                f"We've found the following filter strings do you give the number you want to use. Leave empty if you want to provide a different one\n{filter_str_options}\n"
            )
            if response:
                if response.isnumeric():
                    filter_str = filter_str_list[int(response)]
                else:
                    filter_str = response
        importing_module_file_name_input = input(
            f"Where do you want your usage? [./{importing_module_file_name}]:"
        )
        if importing_module_file_name_input:
            importing_module_file_name = importing_module_file_name_input

        if not filter_str:
            filter_str = input("please provide a filter str [*]") or "*"

        render_from_template(
            "tf-module-usage.tf",
            {
                "module_name": importing_module_name,
                "module_path": args.module_path,
                "service": service_name,
                "filter_str": filter_str,
            },
            importing_module_file_name,
        )

    generate_module(
        module_path=args.module_path,
        service_name=service_name,
        min_provider_version=args.provider_version,
    )

    if tf_imports and input_question(
        "import existing monitors to terraform state?", default_value="N"
    ):
        terraform_init()
        if generate_module_usage:
            using_module = f"module.{importing_module_name}"
        else:
            using_module = input(
                "Please supply the path of the module that uses the new module:"
            )
        for import_item, monitor_id in tf_imports:
            terraform_import(f"{using_module}.{import_item}", monitor_id)


def add_sub_parser(subparsers):
    parser = subparsers.add_parser("module")
    parser.add_argument(
        "module_path", help="The full path of the module eg ./modules/mymodule"
    )
    parser.add_argument("--service_name", help="Name of the service", default=None)
    parser.add_argument(
        "--provider_version", help="Minimal version of datadog provider", default="3.12"
    )
    parser.add_argument(
        "--from_query",
        help="provide a query string like you would in the datadog UI to search for monitors. All results will be added in the new module",
        default=None,
    )
    defaults = load_search_replace_defaults()
    for ky, vl in defaults.items():
        parser.add_argument(f"--{ky}")
    parser.set_defaults(func=main)
