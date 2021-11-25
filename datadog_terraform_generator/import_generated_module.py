import sys
from os.path import join, isfile

from datadog_terraform_generator.generate_tf_module import IMPORT_SUGGESTIONS_FILE_NAME
from datadog_terraform_generator.terraform_calls import terraform_init, terraform_import


def import_generated_module(module_path, using_module_name):
    import_suggestions_path = join(module_path, IMPORT_SUGGESTIONS_FILE_NAME)
    if not isfile(import_suggestions_path):
        print(
            "Import suggestions file is required to find the correct monitor ids for the terraform resources"
        )
        sys.exit()

    tf_imports = []
    with open(import_suggestions_path, "r") as fl:
        for line in fl.readlines():
            if line.strip().startswith("#"):
                continue
            import_item, monitor_id = line.strip().split(";")
            tf_imports.append((import_item, monitor_id))

    terraform_init()
    for import_item, monitor_id in tf_imports:
        terraform_import(f"{using_module_name}.{import_item}", monitor_id)


def main(args):
    import_generated_module(args.module_path, args.using_module_name)


def add_sub_parser(subparsers):
    parser = subparsers.add_parser("import_generated_module")
    parser.add_argument(
        "module_path", help="The full path of the module eg ./modules/mymodule"
    )
    parser.add_argument(
        "using_module_name", help="using module name eg. module.postgres"
    )
    parser.set_defaults(func=main)
