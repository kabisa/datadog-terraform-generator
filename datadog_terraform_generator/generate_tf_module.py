from os.path import join

from datadog_terraform_generator.gen_utils import (
    get_arg_parser,
    get_package_file_contents,
    fill_template,
)


def write_module_file(module_path, file_name, contents, replacements):
    replaced_contents = fill_template(contents, replacements)
    with open(join(module_path, file_name), "w") as fl:
        fl.write(replaced_contents)


def generate_module(module_path, service_name, min_provider_version):
    replacements = {
        "MIN_PROVIDER_VERSION": min_provider_version,
        "SERVICE_NAME": service_name,
    }
    files = [
        ("tf-module-provider", "provider.tf"),
        ("tf-module-variables", "variables.tf"),
    ]
    for packaged_file, output_file in files:
        tf = get_package_file_contents(packaged_file)
        write_module_file(module_path, output_file, tf, replacements)

    # empty main.tf
    write_module_file(module_path, "main.tf", "\n", {})


def main():
    parser = get_arg_parser()
    parser.add_argument(
        "module_path", help="The full path of the module eg ./modules/mymodule"
    )
    parser.add_argument("--service_name", help="Name of the service", default=None)
    parser.add_argument(
        "--provider_version", help="Minimal version of datadog provider", default="2.21"
    )
    args = parser.parse_args()
    generate_module(
        module_path=args.module_path,
        service_name=args.service_name,
        min_provider_version=args.provider_version,
    )


if __name__ == "__main__":
    main()
