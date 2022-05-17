import yaml

from datadog_terraform_generator.api import DdApi
from datadog_terraform_generator.config_management import get_config_by_name


COMMAND_NAME = "services_file"
FILE_NAME_ARG = "--file_name"


def get_services(dd_api: DdApi, env):
    return dd_api.request(path=f"api/v1/service_dependencies?env={env}")


def generate(dd_api, envs, file_name, config_name):
    uncleaned_deps = {}
    for env in envs.split(","):
        services = get_services(dd_api, env=env)
        for service_name, service_dct in services.items():
            uncleaned_deps[service_name] = service_dct["calls"]

    dependees = {}
    service_dependencies = {"depends_on": uncleaned_deps, "dependees": dependees}

    for service, depends_ons in uncleaned_deps.items():
        # this makes sure all services are listed
        if service not in dependees:
            dependees[service] = []
        for depends_on in depends_ons:
            # make sure this service also exists
            if depends_on not in dependees:
                dependees[depends_on] = []
            dependees[depends_on].append(service)

    with open(file_name, "w") as service_calls_fl:
        service_calls_fl.write(
            "# This file is generated with the following command:\n"
            f"# ddtfgen --config {config_name} {COMMAND_NAME} {envs} {FILE_NAME_ARG} {file_name}\n"
        )
        yaml.safe_dump(service_dependencies, service_calls_fl, sort_keys=True)
        print("Written", file_name)


def main(args):
    config = get_config_by_name(args.config_name)
    generate(
        dd_api=DdApi.from_config(config),
        envs=args.envs,
        file_name=args.file_name,
        config_name=args.config_name,
    )


def add_sub_parser(subparsers):
    parser = subparsers.add_parser(COMMAND_NAME)
    parser.add_argument(
        "envs", help="env names you want to be included, separated by a comma"
    )
    parser.add_argument(FILE_NAME_ARG, default="datadog_services.yaml")
    parser.set_defaults(func=main)
