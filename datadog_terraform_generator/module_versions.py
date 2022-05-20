import os
import re

import requests


def get_terraform_files(folder: str):
    subfolders, files = [], []

    for f in os.scandir(folder):
        if f.name == ".terraform":
            continue

        if f.is_dir():
            subfolders.append(f.path)
        if f.is_file():
            if os.path.splitext(f.name)[1].lower() == ".tf":
                if f.name == "provider.tf":
                    continue
                files.append(f.path)

    for folder in list(subfolders):
        sf, f = get_terraform_files(folder)
        subfolders.extend(sf)
        files.extend(f)

    return subfolders, files


def get_modules_in_file(scan_folder, file_path):
    with open(os.path.join(scan_folder, file_path), "r") as fl:
        module_usage_name = None
        module_name = None
        source = None
        version = None
        for line in fl.readlines():
            if m := re.match(r'\s*module\s+"([^"]+)"\s+\{', line):
                module_usage_name = m.group(1)
            elif m := re.match(r'\s*source\s*=\s*"([^"]+)"', line):
                source = m.group(1)
                if "=" in source:
                    source, version = source.split("=")
                    source = source.split(".git")[0]
                    source = source.replace(
                        "git@github.com:kabisa/terraform-datadog-", ""
                    )
                    module_name = source
                    yield file_path, module_name, module_name, version
                else:
                    if source.startswith(".."):
                        continue  # relative module
            elif m := re.match(r'\s*version\s+=\s*"([^"]+)"', line):
                version = m.group(1)
                module_name = source
                if "/" in module_name:
                    module_name = module_name.split("/")[1]
                yield file_path, module_usage_name, module_name, version


def scan_module_versions(args):
    scan_folder = args.path
    _, files = get_terraform_files(scan_folder)
    files = [os.path.relpath(file, scan_folder) for file in files]
    for file in files:
        for file_path, module_usage_name, module_name, version in get_modules_in_file(
            scan_folder, file
        ):
            print(file_path, module_usage_name, module_name, version)


def get_next_url(data, base_url):
    next_url = data["meta"].get("next_url")
    if next_url:
        next_url = next_url.split("///")[-1]
        return f"{base_url}/{next_url}"


def list_module_versions(args):
    modules = get_kabisa_datadog_modules()
    for module in modules:
        maker, module_name, provider, version = module["id"].split("/")
        print(module_name, version)


def get_kabisa_datadog_modules():
    modules = []
    base_url = "https://registry.terraform.io"
    req = requests.get(f"{base_url}/v1/modules?provider=datadog")
    data = req.json()
    for module in data["modules"]:
        if module["id"].startswith("kabisa"):
            modules.append(module)
    next_url = get_next_url(data, base_url)
    while next_url:
        req = requests.get(next_url)
        data = req.json()
        for module in data["modules"]:
            if module["id"].startswith("kabisa"):
                modules.append(module)
        next_url = get_next_url(data, base_url)
    return modules


def show_module_drift(args):
    modules = get_kabisa_datadog_modules()
    existing = {}
    for module in modules:
        maker, module_name, provider, version = module["id"].split("/")
        existing[module_name] = tuple(version.split("."))

    scan_folder = args.path
    _, files = get_terraform_files(scan_folder)
    files = [os.path.relpath(file, scan_folder) for file in files]
    for file in files:
        for file_path, module_usage_name, module_name, version in get_modules_in_file(
            scan_folder, file
        ):
            version = tuple(version.split("."))
            tf_registry_version = existing.get(module_name)
            if tf_registry_version and version < tf_registry_version:
                print(
                    file_path,
                    module_name,
                    module_usage_name,
                    ".".join(version),
                    "<",
                    ".".join(tf_registry_version),
                )
            if not tf_registry_version:
                print(file_path, module_name, ".".join(version), "?")


def add_sub_parser(subparsers):
    parser = subparsers.add_parser("scan-module-versions")
    parser.add_argument("path")
    parser.set_defaults(func=scan_module_versions)

    parser = subparsers.add_parser("list-module-versions")
    parser.set_defaults(func=list_module_versions)

    parser = subparsers.add_parser("show-module-drift")
    parser.add_argument("path")
    parser.set_defaults(func=show_module_drift)
