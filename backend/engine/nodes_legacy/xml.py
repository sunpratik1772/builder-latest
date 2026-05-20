"""XML node converting json<->xml for item fields."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _to_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return [value] if value is not None else []


def _dict_to_xml_element(tag: str, value: Any) -> ET.Element:
    el = ET.Element(tag)
    if isinstance(value, dict):
        for k, v in value.items():
            if k.startswith("@"):
                el.set(k[1:], "" if v is None else str(v))
            elif k == "#text":
                el.text = "" if v is None else str(v)
            elif isinstance(v, list):
                for item in v:
                    el.append(_dict_to_xml_element(k, item))
            else:
                el.append(_dict_to_xml_element(k, v))
    elif isinstance(value, list):
        for item in value:
            el.append(_dict_to_xml_element("item", item))
    elif value is not None:
        el.text = str(value)
    return el


def _xml_element_to_obj(
    el: ET.Element,
    *,
    attrkey: str,
    charkey: str,
    explicit_array: bool,
    ignore_attrs: bool,
    normalize_tags: bool,
    trim: bool,
) -> Any:
    tag = el.tag.lower() if normalize_tags else el.tag
    children = list(el)
    data: dict[str, Any] = {}
    if not ignore_attrs and el.attrib:
        data[attrkey] = dict(el.attrib)
    text = (el.text or "").strip() if trim else (el.text or "")
    if text:
        data[charkey] = text
    for c in children:
        c_obj = _xml_element_to_obj(
            c,
            attrkey=attrkey,
            charkey=charkey,
            explicit_array=explicit_array,
            ignore_attrs=ignore_attrs,
            normalize_tags=normalize_tags,
            trim=trim,
        )
        c_tag = next(iter(c_obj.keys()))
        c_val = c_obj[c_tag]
        if c_tag in data:
            if not isinstance(data[c_tag], list):
                data[c_tag] = [data[c_tag]]
            data[c_tag].append(c_val)
        else:
            data[c_tag] = [c_val] if explicit_array else c_val
    if not children and set(data.keys()) == {charkey}:
        return {tag: data[charkey]}
    if not children and not data:
        return {tag: text}
    return {tag: data}


def handle_xml(node: dict, ctx: RunContext) -> None:
    """Convert XML <-> JSON on configured property."""
    cfg = node.get("config", {}) or {}
    node_id = node.get("id", "xml")
    src = ctx.get(f"{node_id}_input", [])
    items = _to_list(src)
    mode = str(cfg.get("mode", "xmlToJson"))
    prop = str(cfg.get("dataPropertyName", cfg.get("property_name", "data")))
    options = cfg.get("options", {}) or {}

    attrkey = str(options.get("attrkey", "@"))
    charkey = str(options.get("charkey", "#text"))

    out: list[dict[str, Any]] = []
    for item in items:
        row = item if isinstance(item, dict) else {"value": item}
        if mode == "jsonToxml":
            root_name = str(options.get("rootName", "root"))
            root = _dict_to_xml_element(root_name, row)
            xml_text = ET.tostring(root, encoding="unicode")
            if not bool(options.get("headless", False)):
                xml_text = '<?xml version="1.0" encoding="UTF-8"?>' + xml_text
            out.append({prop: xml_text})
        else:
            xml_text = row.get(prop)
            if not isinstance(xml_text, str):
                raise ValueError(f'Item has no XML string in property "{prop}"')
            root = ET.fromstring(xml_text)
            parsed = _xml_element_to_obj(
                root,
                attrkey=attrkey,
                charkey=charkey,
                explicit_array=bool(options.get("explicitArray", False)),
                ignore_attrs=bool(options.get("ignoreAttrs", False)),
                normalize_tags=bool(options.get("normalizeTags", False)),
                trim=bool(options.get("trim", False)),
            )
            if bool(options.get("explicitRoot", True)):
                out.append(parsed)
            else:
                out.append(next(iter(parsed.values())))

    ctx.set(f"{node_id}_output", out)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_xml)
