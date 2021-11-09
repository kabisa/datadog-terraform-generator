from datadog_terraform_generator.terraform_calls import terraform_plan

DESTROY_SEQ = "\033[0m will be \033[1m\033[31mdestroyed\033[0m\033[0m"
DESTROY_SEQ_LEN = len(DESTROY_SEQ)
CREATE_SEQ = "\033[0m will be created\033[0m\033[0m"
CREATE_SEQ_LEN = len(CREATE_SEQ)
INPLACE_SEQ = "\033[0m will be updated in-place\033[0m\033[0m"
INPLACE_SEQ_LEN = len(INPLACE_SEQ)


def get_terraform_changes():
    output = terraform_plan()
    lines = output.splitlines(keepends=False)
    actions_idx = lines.index("Terraform will perform the following actions:")
    lines = lines[actions_idx:]

    in_places = [
        line[8:-INPLACE_SEQ_LEN] for line in lines if line.endswith(INPLACE_SEQ)
    ]
    if in_places:
        print("\nIn place changes:")
        print("\n".join(sorted(in_places)))

    destroys = [
        line[8:-DESTROY_SEQ_LEN] for line in lines if line.endswith(DESTROY_SEQ)
    ]
    if destroys:
        print("\nDestroys:")
        print("\n".join(sorted(destroys)))

    creates = [line[8:-CREATE_SEQ_LEN] for line in lines if line.endswith(CREATE_SEQ)]
    if creates:
        print("\nCreates:")
        print("\n".join(sorted(creates)))

    print("")


def main(args):
    get_terraform_changes()


def add_sub_parser(subparsers):
    parser = subparsers.add_parser("get_terraform_changes")
    parser.set_defaults(func=main)
