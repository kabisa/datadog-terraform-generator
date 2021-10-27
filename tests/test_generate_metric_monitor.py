import json

from mock import patch, mock_open
from mock import Mock, call


def get_fixture(name):
    with open(f"fixtures/{name}", "r") as fl:
        return fl.read()


MW = mock_open()


def mocked_writes():
    def wrapper(file_path, mode):
        if "w" in mode:
            return MW(file_path, mode)
        else:
            return open(file_path, mode)

    m = Mock()
    m.side_effect = wrapper

    return m


@patch(
    "datadog_terraform_generator.generate_tf_monitor.open", new_callable=mocked_writes
)
@patch("datadog_terraform_generator.config_management.get_config_by_name")
@patch("datadog_terraform_generator.api.DdApi")
def test_generate_metrics_monitor(DdApi, get_config_by_name, mocked_open):
    get_config_by_name.return_value = {}

    args = Mock()
    args.config_name = "tme"
    args.monitor_id = 2001855
    args.output_dir = "/tmp/"

    mock_api = Mock()
    mock_api.request.return_value = json.loads(get_fixture("2001855.json"))
    DdApi.from_config.return_value = mock_api

    from datadog_terraform_generator.generate_tf_monitor_from_id import main

    main(args)
    calls = [call("/tmp/lock-waits-variables.tf", "w"), call("/tmp/lock-waits.tf", "w")]
    mocked_open.assert_has_calls(calls, any_order=True)

    write_calls = [
        call(get_fixture("lock-waits-variables.tf")),
        call(get_fixture("lock-waits.tf")),
    ]
    MW().write.assert_has_calls(write_calls, any_order=True)
