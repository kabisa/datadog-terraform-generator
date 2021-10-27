from datadog_terraform_generator.terraform_calls import get_state_list, move_state


def mass_move(old_state_prefix, new_state_prefix):
    state_list = get_state_list()
    for resource_path in state_list:
        if resource_path.startswith(old_state_prefix):
            sz = len(old_state_prefix)
            rest = resource_path[sz:]
            new = f"{new_state_prefix}{rest}"
            print(resource_path, new)
            move_state(old=resource_path, new=new)


def main(args):
    mass_move(args.old_state_prefix, args.new_state_prefix)


def add_sub_parser(subparsers):
    parser = subparsers.add_parser("mass_state_move")
    parser.add_argument("old_state_prefix", help="example: module.x.y.")
    parser.add_argument("new_state_prefix", help="example: module.a.b.")
    parser.set_defaults(func=main)
