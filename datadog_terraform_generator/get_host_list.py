import json

import math
from fnmatch import fnmatch

from datadog_terraform_generator.api import DdApi
from datadog_terraform_generator.config_management import get_config_by_name


def get_host_list(dd_api: DdApi, host_name_pattern=None, tags_pattern=None):
    if host_name_pattern:
        host_name_pattern = host_name_pattern.lower()
    if tags_pattern:
        tags_pattern = tags_pattern.lower()

    page_size = 1000
    hosts = dd_api.request(f"api/v1/hosts?count={page_size}")
    number_subsequent_requests = math.ceil(
        (hosts["total_matching"] - hosts["total_returned"]) / page_size
    )
    yield from filter_hosts(host_name_pattern, hosts, tags_pattern)
    for call_nr in range(number_subsequent_requests):
        start = (call_nr + 1) * page_size
        hosts = dd_api.request(f"api/v1/hosts?count={page_size}&start={start}")
        yield from filter_hosts(host_name_pattern, hosts, tags_pattern)


def tags_match(tags, tags_pattern):
    for matchable_pattern in tags_pattern.split(","):
        pattern_key, pattern_value = matchable_pattern.split(":")
        for tag in tags:
            if ":" in tag:
                tag_key, tag_value = tag.split(":", maxsplit=1)
                if tag_key == pattern_key and fnmatch(tag_value, pattern_value):
                    return True
    return False


def filter_hosts(host_name_pattern, hosts, tags_pattern):
    for host in hosts["host_list"]:
        name = host["name"].lower()
        if host_name_pattern and not fnmatch(name, host_name_pattern):
            continue

        tags = get_tags_from_host(host)
        if tags_pattern and not tags_match(tags, tags_pattern):
            continue
        yield host


def get_ip_from_gohai(gohai):
    if gohai and gohai.get("network"):
        return gohai["network"].get("ipaddress", "")


def print_hosts(hosts):
    cnt = 0
    for host in sorted(hosts, key=lambda h: (get_env_from_host(h), h["name"])):
        cnt += 1
        tags = get_tags_from_host(host)
        if "gohai" in host["meta"]:
            gohai = json.loads(host["meta"]["gohai"])
            ip_address = get_ip_from_gohai(gohai)
            print(host["name"], tags, ip_address)
        else:
            print(host["name"], tags)
    print(f"Found {cnt} hosts")


def get_env_from_host(host):
    return get_env(get_tags_from_host(host))


def get_env(tags):
    for tag in tags:
        if tag.startswith("env:"):
            return tag[4:]
    return ""


def get_tags_from_host(host):
    all_tags = []
    tbs = host["tags_by_source"]
    for ky, tags in tbs.items():
        all_tags.extend(tags)
    return list(sorted(set(all_tags)))


def main(args):
    config = get_config_by_name(args.config_name)
    print_hosts(
        get_host_list(
            dd_api=DdApi.from_config(config),
            host_name_pattern=args.host_name_pattern,
            tags_pattern=args.tags_pattern,
        )
    )


def add_sub_parser(subparsers):
    parser = subparsers.add_parser("get_host_list")
    parser.add_argument(
        "--host_name_pattern",
        help="""Give the pattern with which the host name needs to match
             Patterns are Unix shell style:
             *       matches everything
             ?       matches any single character
             [seq]   matches any character in seq
             [!seq]  matches any char not in seq
             """,
    )
    parser.add_argument(
        "--tags_pattern",
        help="""Give the pattern with which the host tags needs to match
             multiple values can be supplied like: "ky:vl,k2:someth*"
             Patterns are Unix shell style:
             *       matches everything
             ?       matches any single character
             [seq]   matches any character in seq
             [!seq]  matches any char not in seq
             """,
    )
    parser.set_defaults(func=main)
