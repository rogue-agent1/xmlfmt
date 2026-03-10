#!/usr/bin/env python3
"""xmlfmt - XML formatter, validator, and query tool.

One file. Zero deps. Tame your XML.

Usage:
  xmlfmt.py pretty file.xml          → pretty-print
  xmlfmt.py mini file.xml            → minify
  xmlfmt.py validate file.xml        → check well-formedness
  xmlfmt.py xpath file.xml "//tag"   → XPath query
  xmlfmt.py tags file.xml            → list all tag names
  xmlfmt.py to-json file.xml         → convert to JSON
  cat file.xml | xmlfmt.py pretty -  → stdin
"""

import argparse
import json
import sys
import xml.dom.minidom
import xml.etree.ElementTree as ET


def read_xml(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    with open(path) as f:
        return f.read()


def cmd_pretty(args):
    text = read_xml(args.file)
    dom = xml.dom.minidom.parseString(text)
    print(dom.toprettyxml(indent="  "))


def cmd_mini(args):
    text = read_xml(args.file)
    root = ET.fromstring(text)
    print(ET.tostring(root, encoding="unicode"))


def cmd_validate(args):
    text = read_xml(args.file)
    try:
        ET.fromstring(text)
        print("✅ Well-formed XML")
    except ET.ParseError as e:
        print(f"❌ Invalid XML: {e}", file=sys.stderr)
        return 1


def cmd_xpath(args):
    text = read_xml(args.file)
    root = ET.fromstring(text)
    results = root.findall(args.expr)
    if not results:
        print("No matches")
        return
    for elem in results:
        if elem.text and elem.text.strip():
            print(f"  <{elem.tag}> {elem.text.strip()}")
        else:
            print(f"  <{elem.tag}> ({len(list(elem))} children)")


def cmd_tags(args):
    text = read_xml(args.file)
    root = ET.fromstring(text)
    tags = set()
    for elem in root.iter():
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        tags.add(tag)
    for tag in sorted(tags):
        count = len(root.findall(f".//{tag}"))
        print(f"  {tag:30s} {count}x")


def elem_to_dict(elem) -> dict | str:
    d = {}
    if elem.attrib:
        d["@attributes"] = dict(elem.attrib)
    children = list(elem)
    if not children:
        text = (elem.text or "").strip()
        if d:
            if text:
                d["#text"] = text
            return d
        return text
    for child in children:
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        val = elem_to_dict(child)
        if tag in d:
            if not isinstance(d[tag], list):
                d[tag] = [d[tag]]
            d[tag].append(val)
        else:
            d[tag] = val
    return d


def cmd_to_json(args):
    text = read_xml(args.file)
    root = ET.fromstring(text)
    tag = root.tag.split("}")[-1] if "}" in root.tag else root.tag
    result = {tag: elem_to_dict(root)}
    print(json.dumps(result, indent=2, ensure_ascii=False))


def main():
    p = argparse.ArgumentParser(description="XML formatter and query tool")
    sub = p.add_subparsers(dest="cmd")

    for name in ("pretty", "mini", "validate", "tags", "to-json"):
        s = sub.add_parser(name)
        s.add_argument("file")

    s = sub.add_parser("xpath")
    s.add_argument("file")
    s.add_argument("expr")

    args = p.parse_args()
    if not args.cmd:
        p.print_help()
        return 1
    cmds = {"pretty": cmd_pretty, "mini": cmd_mini, "validate": cmd_validate,
            "xpath": cmd_xpath, "tags": cmd_tags, "to-json": cmd_to_json}
    return cmds[args.cmd](args) or 0


if __name__ == "__main__":
    sys.exit(main())
