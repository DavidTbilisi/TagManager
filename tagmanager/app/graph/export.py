import xml.etree.ElementTree as ET
from datetime import date
from typing import Dict


def _hex_to_rgb(hex_color: str):
    h = hex_color.lstrip("#")
    if len(h) == 6:
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return 128, 128, 128


def to_gexf(graph_data: dict, directed: bool = False) -> str:
    edge_type = "directed" if directed else "undirected"
    today = date.today().isoformat()

    gexf = ET.Element("gexf", {
        "xmlns": "http://gexf.net/1.3",
        "xmlns:viz": "http://gexf.net/1.3/viz",
        "version": "1.3",
    })

    meta = ET.SubElement(gexf, "meta", {"lastmodifieddate": today})
    ET.SubElement(meta, "creator").text = "TagManager"
    ET.SubElement(meta, "description").text = (
        f"Tag {graph_data.get('meta', {}).get('mode', 'tag')} network — "
        f"{graph_data.get('meta', {}).get('node_count', 0)} nodes, "
        f"{graph_data.get('meta', {}).get('edge_count', 0)} edges"
    )

    graph = ET.SubElement(gexf, "graph", {"defaultedgetype": edge_type})

    # Node attribute declarations
    node_attrs = ET.SubElement(graph, "attributes", {"class": "node"})
    ET.SubElement(node_attrs, "attribute", {"id": "0", "title": "node_type", "type": "string"})
    ET.SubElement(node_attrs, "attribute", {"id": "1", "title": "size", "type": "float"})
    ET.SubElement(node_attrs, "attribute", {"id": "2", "title": "cluster", "type": "integer"})
    ET.SubElement(node_attrs, "attribute", {"id": "3", "title": "file_count", "type": "integer"})
    ET.SubElement(node_attrs, "attribute", {"id": "4", "title": "path", "type": "string"})
    ET.SubElement(node_attrs, "attribute", {"id": "5", "title": "extension", "type": "string"})

    # Edge attribute declarations
    edge_attrs = ET.SubElement(graph, "attributes", {"class": "edge"})
    ET.SubElement(edge_attrs, "attribute", {"id": "0", "title": "label", "type": "string"})

    nodes_el = ET.SubElement(graph, "nodes")
    for n in graph_data.get("nodes", []):
        node_el = ET.SubElement(nodes_el, "node", {
            "id": str(n["id"]),
            "label": str(n["label"]),
        })
        attvalues = ET.SubElement(node_el, "attvalues")
        meta_d = n.get("metadata", {})
        ET.SubElement(attvalues, "attvalue", {"for": "0", "value": str(n.get("type", ""))})
        ET.SubElement(attvalues, "attvalue", {"for": "1", "value": str(round(n.get("size", 1.0), 3))})
        ET.SubElement(attvalues, "attvalue", {"for": "2", "value": str(n.get("group", 0))})
        ET.SubElement(attvalues, "attvalue", {"for": "3", "value": str(meta_d.get("file_count", 0))})
        ET.SubElement(attvalues, "attvalue", {"for": "4", "value": str(meta_d.get("path", ""))})
        ET.SubElement(attvalues, "attvalue", {"for": "5", "value": str(meta_d.get("extension", ""))})

        r, g, b = _hex_to_rgb(n.get("color", "#888888"))
        ET.SubElement(node_el, "viz:color", {"r": str(r), "g": str(g), "b": str(b)})
        ET.SubElement(node_el, "viz:size", {"value": str(round(n.get("size", 1.0), 3))})

    edges_el = ET.SubElement(graph, "edges")
    for i, e in enumerate(graph_data.get("edges", [])):
        edge_el = ET.SubElement(edges_el, "edge", {
            "id": f"e{i}",
            "source": str(e["source"]),
            "target": str(e["target"]),
            "weight": str(round(e.get("weight", 1.0), 4)),
        })
        attvalues = ET.SubElement(edge_el, "attvalues")
        ET.SubElement(attvalues, "attvalue", {"for": "0", "value": str(e.get("label", ""))})

    ET.indent(gexf, space="  ")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(gexf, encoding="unicode")


def to_graphml(graph_data: dict, directed: bool = False) -> str:
    edge_default = "directed" if directed else "undirected"

    graphml = ET.Element("graphml", {
        "xmlns": "http://graphml.graphdrawing.org/graphml",
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "xsi:schemaLocation": (
            "http://graphml.graphdrawing.org/graphml "
            "http://graphml.graphdrawing.org/graphml/1.0/graphml.xsd"
        ),
    })

    # Key declarations
    keys = [
        ("d0", "node", "label",      "string"),
        ("d1", "node", "node_type",  "string"),
        ("d2", "node", "size",       "double"),
        ("d3", "node", "cluster",    "int"),
        ("d4", "node", "file_count", "int"),
        ("d5", "node", "path",       "string"),
        ("d6", "node", "extension",  "string"),
        ("d7", "node", "color",      "string"),
        ("d8", "edge", "weight",     "double"),
        ("d9", "edge", "label",      "string"),
    ]
    for kid, for_el, name, atype in keys:
        ET.SubElement(graphml, "key", {
            "id": kid, "for": for_el,
            "attr.name": name, "attr.type": atype,
        })

    graph = ET.SubElement(graphml, "graph", {"id": "G", "edgedefault": edge_default})

    for n in graph_data.get("nodes", []):
        node_el = ET.SubElement(graph, "node", {"id": str(n["id"])})
        meta_d = n.get("metadata", {})
        pairs = [
            ("d0", str(n["label"])),
            ("d1", str(n.get("type", ""))),
            ("d2", str(round(n.get("size", 1.0), 3))),
            ("d3", str(n.get("group", 0))),
            ("d4", str(meta_d.get("file_count", 0))),
            ("d5", str(meta_d.get("path", ""))),
            ("d6", str(meta_d.get("extension", ""))),
            ("d7", str(n.get("color", "#888888"))),
        ]
        for key, val in pairs:
            d = ET.SubElement(node_el, "data", {"key": key})
            d.text = val

    for i, e in enumerate(graph_data.get("edges", [])):
        edge_el = ET.SubElement(graph, "edge", {
            "id": f"e{i}",
            "source": str(e["source"]),
            "target": str(e["target"]),
        })
        dw = ET.SubElement(edge_el, "data", {"key": "d8"})
        dw.text = str(round(e.get("weight", 1.0), 4))
        dl = ET.SubElement(edge_el, "data", {"key": "d9"})
        dl.text = str(e.get("label", ""))

    ET.indent(graphml, space="  ")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(graphml, encoding="unicode")


def save_export(content: str, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
