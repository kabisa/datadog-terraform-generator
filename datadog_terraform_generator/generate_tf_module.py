from os.path import join

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
    generate_module(
        module_path=args.module_path,
        service_name=args.service_name,
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
    parser.set_defaults(func=main)
