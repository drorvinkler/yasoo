from functools import partial
from typing import Iterable, Dict, Callable, cast

from more_itertools.recipes import consume


def remove_type_data(data, type_key: str) -> None:
    callback = cast(
        Callable[[dict], None], partial(_delete_type_key, type_key=type_key)
    )
    _iterate_data(data, callback)


def rename_types(data, type_key: str, rename_map: Dict[str, str]) -> None:
    callback = cast(
        Callable[[dict], None],
        partial(_rename_types, type_key=type_key, rename_map=rename_map),
    )
    _iterate_data(data, callback)


def _iterate_data(data, callback: Callable[[dict], None]) -> None:
    if isinstance(data, dict):
        callback(data)
        consume(_iterate_data(v, callback) for v in data.values())
    elif isinstance(data, Iterable) and not isinstance(data, str):
        consume(_iterate_data(i, callback) for i in data)


def _delete_type_key(data: dict, type_key: str) -> None:
    data.pop(type_key, None)


def _rename_types(data: dict, type_key: str, rename_map: Dict[str, str]) -> None:
    if type_key not in data:
        return
    renamed = rename_map.get(data[type_key])
    if renamed is not None:
        data[type_key] = renamed


def _add_sub_parser_common_args(sub_parser):
    sub_parser.add_argument(
        "-i", "--infile", type=argparse.FileType("r"), required=True
    )
    sub_parser.add_argument(
        "-o", "--outfile", type=argparse.FileType("w"), required=True
    )


def _exec_remove_type_data(data, args):
    remove_type_data(data, args.type_key)


def _exec_rename_types(data, args):
    rename_map = dict(r.split(":") for r in args.rename_map)
    rename_types(data, args.type_key, rename_map)


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Fix serialized data to reflect changes in the code."
    )
    sub_parsers = parser.add_subparsers()

    parser_del = sub_parsers.add_parser(
        "remove_types",
        description="Deletes the type key from the data, to allow deserialization based on type hints only.",
    )
    _add_sub_parser_common_args(parser_del)
    parser_del.add_argument("-t", "--type-key", type=str, required=True)
    parser_del.set_defaults(func=_exec_remove_type_data)

    parser_rename = sub_parsers.add_parser(
        "rename_types", description="Renames types to reflect changes in the code."
    )
    _add_sub_parser_common_args(parser_rename)
    parser_rename.add_argument("-t", "--type-key", type=str, required=True)
    parser_rename.add_argument(
        "-r",
        "--rename-map",
        nargs="+",
        help="One or more arguments of <old-name>:<new-name>",
    )
    parser_rename.set_defaults(func=_exec_rename_types)

    args = parser.parse_args()

    try:
        data = json.load(args.infile)
        args.func(data, args)
        json.dump(data, args.outfile)
    finally:
        args.infile.close()
        args.outfile.flush()
        args.outfile.close()
