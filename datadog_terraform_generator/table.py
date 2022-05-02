import csv
import locale

from datadog_terraform_generator.api import DdApi
from datadog_terraform_generator.config_management import get_config_by_name
from datadog_terraform_generator.query import query, interpret_time


def table():
    locale.setlocale(category=locale.LC_CTYPE, locale="en_us")
    properties = {
        "aggregation": "max",
        "group_by": ["rabbitmq_queue", "rabbitmq_vhost"],
    }
    metrics = {
        "rabbitmq.queue.messages": properties,
        "rabbitmq.queue.consumers": properties,
        "rabbitmq.queue.messages.rate": properties,
        "rabbitmq.queue.memory": properties,
        "rabbitmq.queue.messages.publish.rate": properties,
        "rabbitmq.queue.messages.get.rate": properties,
    }
    config = get_config_by_name(None)
    dd_api = DdApi.from_config(config)
    _from = interpret_time("1 hours ago")
    to = interpret_time("now")
    filter_str = "*"

    output = []
    for metric_name, metric_properties in metrics.items():
        aggregation = metric_properties["aggregation"]
        group_bys = metric_properties.get("group_by", "")
        if group_bys:
            group_by = " by {" + ",".join(group_bys) + "}"
        else:
            group_by = ""
        query_res = query(
            _from=_from,
            to=to,
            qry=f"{aggregation}:{metric_name}{{{filter_str}}}{group_by}",
            dd_api=dd_api,
        )
        for item in query_res["series"]:
            for point in item["pointlist"]:
                output.append(
                    [item["metric"], '"' + ",".join(item["tag_set"]) + '"'] + point
                )

    with open("tmp.csv", "w") as fl:
        writer = csv.writer(fl)
        writer.writerows(output)


if __name__ == "__main__":
    table()
