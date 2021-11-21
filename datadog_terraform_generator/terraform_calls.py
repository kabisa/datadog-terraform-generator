from datadog_terraform_generator.gen_utils import cli_call


def get_state_list():
    output = cli_call(["terraform", "state", "list"])
    state_list = output.splitlines(keepends=False)
    return state_list


def move_state(old: str, new: str):
    cli_call(["terraform", "state", "mv", old, new])


def terraform_plan(target=None):
    args = ["terraform", "plan"]
    if target:
        args.extend(["--target", target])
    return cli_call(args)
