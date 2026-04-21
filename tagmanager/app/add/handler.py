from .service import add_tags


def _cli_bool(obj, name: str) -> bool:
    """True only when attribute is literally True (avoids MagicMock truthiness)."""
    v = getattr(obj, name, False)
    return v is True


def handle_add_command(args):
    apply_aliases = not _cli_bool(args, "no_aliases")
    auto_tag = not _cli_bool(args, "no_auto")
    content_tag = not _cli_bool(args, "no_content")
    add_tags(
        args.file,
        args.tags,
        apply_aliases=apply_aliases,
        auto_tag=auto_tag,
        content_tag=content_tag,
    )
