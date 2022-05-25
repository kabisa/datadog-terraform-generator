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


def version_tuple(version):
    parts = version.split(".")
    version_list = []
    for part in parts:
        if part.isnumeric():
            version_list.append(int(part))
        else:
            version_list.append(part)
    return tuple(version_list)


def should_update_version(version, registry_version, safe_option=True) -> bool:
    if not registry_version:
        return False
    if len(version) == 1:
        return True
    try:
        return version < registry_version
    except Exception:
        min_len = min(len(version), 3)
        for i in range(min_len):
            if isinstance(version[i], int):
                if version[i] < registry_version[i]:
                    return True
            else:
                return safe_option


def version_tuple_str(version_tup) -> str:
    return ".".join(map(str, version_tup))


def show_module_drift(args):
    modules = get_kabisa_datadog_modules()
    existing = {}
    for module in modules:
        maker, module_name, provider, version = module["id"].split("/")
        existing[module_name] = version_tuple(version)

    scan_folder = args.path
    _, files = get_terraform_files(scan_folder)
    files = [os.path.relpath(file, scan_folder) for file in files]
    for file in files:
        for file_path, module_usage_name, module_name, version in get_modules_in_file(
            scan_folder, file
        ):
            version = version_tuple(version)
            tf_registry_version = existing.get(module_name)
            if should_update_version(version, tf_registry_version):
                print(
                    file_path,
                    module_name,
                    module_usage_name,
                    version_tuple_str(version),
                    "!=",
                    version_tuple_str(tf_registry_version),
                )
            if not tf_registry_version:
                print(file_path, module_name, version_tuple_str(version), "?")


def upgrade_modules_in_file(scan_folder, file_path, registry):
    lines = []
    with open(os.path.join(scan_folder, file_path), "r") as fl:
        module_name = None
        source = None
        version = None
        original_lines = fl.read().splitlines()
        for line in original_lines:
            if m := re.match(r'\s*source\s*=\s*"([^"]+)"', line):
                source = m.group(1)
                if "=" in source:
                    source, version = source.split("=")
                    source = source.split(".git")[0]
                    source = source.replace(
                        "git@github.com:kabisa/terraform-datadog-", ""
                    )
                    module_name = source
                    tf_registry_version = registry.get(module_name)
                    # regardless of version we put in the registry version
                    new_source_name = f"kabisa/{module_name}/datadog"
                    lines.append(f'  source  = "{new_source_name}"')
                    lines.append(
                        f'  version = "{version_tuple_str(tf_registry_version)}"'
                    )
                else:
                    lines.append(line)
            elif m := re.match(r'\s*version\s+=\s*"([^"]+)"', line):
                version = m.group(1)
                module_name = source
                if "/" in module_name:
                    module_name = module_name.split("/")[1]
                tf_registry_version = registry.get(module_name)
                if should_update_version(version_tuple(version), tf_registry_version):
                    lines.append(
                        f'  version = "{version_tuple_str(tf_registry_version)}"'
                    )
                else:
                    lines.append(line)
            else:
                lines.append(line)
    if lines:
        with open(os.path.join(scan_folder, file_path), "w") as fl:
            if lines[-1].strip() != "":
                # make sure file ends with empty line
                lines.append("")
            fl.write("\n".join(lines))


def upgrade_modules(args):
    modules = get_kabisa_datadog_modules()
    registry = {}
    for module in modules:
        maker, module_name, provider, version = module["id"].split("/")
        registry[module_name] = version_tuple(version)

    scan_folder = args.path
    _, files = get_terraform_files(scan_folder)
    files = [os.path.relpath(file, scan_folder) for file in files]
    for file in files:
        upgrade_modules_in_file(scan_folder, file, registry)


def add_sub_parser(subparsers):
    parser = subparsers.add_parser("scan_module_versions")
    parser.add_argument("path")
    parser.set_defaults(func=scan_module_versions)

    parser = subparsers.add_parser("list_module_versions")
    parser.set_defaults(func=list_module_versions)

    parser = subparsers.add_parser("show_module_drift")
    parser.add_argument("path")
    parser.set_defaults(func=show_module_drift)

    parser = subparsers.add_parser("upgrade_modules")
    parser.add_argument("path")
    parser.set_defaults(func=upgrade_modules)


if __name__ == "__main__":

    class Obj:
        pass

    args = Obj()
    args.path = "/Users/sjuuljanssen/workspace/toyota-dd/modules/termproxy"
    upgrade_modules(args)
