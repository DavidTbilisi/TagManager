from .service import remove_path, remove_invalid_paths


def handle_remove_command(args):
    if args.path:
        r = remove_path(args.path)
        print(r.get("message", ""))
    elif args.invalid:
        r = remove_invalid_paths()
        print(r.get("message", ""))
    else:
        print("No arguments provided")
    return None
