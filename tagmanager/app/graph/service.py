import os
import itertools
import math
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict
from typing import Dict, List, Literal, Tuple

from ..helpers import load_tags
from ..filter.service import calculate_tag_similarity, find_tag_clusters

# Color palette for up to 20 clusters + type defaults
_CLUSTER_COLORS = [
    "#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f",
    "#edc948", "#b07aa1", "#ff9da7", "#9c755f", "#bab0ac",
    "#d37295", "#fabfd2", "#8cd17d", "#b6992d", "#f1ce63",
    "#499894", "#86bcb6", "#e15759", "#79706e", "#d4a6c8",
]
_TYPE_COLORS = {"tag": "#4e79a7", "file": "#59a14f", "folder": "#f28e2b"}
_EXT_COLOR_MAP: Dict[str, str] = {
    "py": "#3572A5", "js": "#f1e05a", "ts": "#2b7489", "tsx": "#2b7489",
    "jsx": "#f1e05a", "html": "#e34c26", "css": "#563d7c", "json": "#292929",
    "md": "#083fa1", "txt": "#89e051", "pdf": "#b30b00", "png": "#a97bff",
    "jpg": "#a97bff", "jpeg": "#a97bff", "gif": "#a97bff", "svg": "#ff9900",
    "sh": "#89e051", "bat": "#C1F12E", "rs": "#dea584", "go": "#00ADD8",
    "java": "#b07219", "c": "#555555", "cpp": "#f34b7d", "rb": "#701516",
    "php": "#4F5D95", "swift": "#ffac45", "kt": "#F18E33", "cs": "#178600",
    "yml": "#cb171e", "yaml": "#cb171e", "toml": "#9c4221", "xml": "#0060ac",
    "csv": "#237346", "xlsx": "#217346", "zip": "#999999", "tar": "#999999",
    "gz": "#999999", "sql": "#e38c00", "db": "#e38c00",
}


@dataclass
class GraphNode:
    id: str
    label: str
    type: Literal["tag", "file", "folder"]
    size: float
    color: str
    group: int
    metadata: dict


@dataclass
class GraphEdge:
    source: str
    target: str
    weight: float
    directed: bool
    label: str


def _log_scale(value: float, max_value: float, min_size: float = 1.0, max_size: float = 5.0) -> float:
    if max_value <= 0:
        return min_size
    return min_size + (max_size - min_size) * math.log1p(value) / math.log1p(max_value)


def _ext_color(path: str) -> str:
    ext = os.path.splitext(path)[1].lstrip(".").lower()
    return _EXT_COLOR_MAP.get(ext, "#888888")


def _cluster_color(group: int) -> str:
    return _CLUSTER_COLORS[group % len(_CLUSTER_COLORS)]


def _node_dict(n: GraphNode) -> dict:
    return asdict(n)


def _edge_dict(e: GraphEdge) -> dict:
    return asdict(e)


def build_tag_graph(min_weight: int = 1) -> dict:
    """
    Build a tag co-occurrence graph.
    Nodes = tags, Edges = pairs of tags that appear on the same file.
    Edge weight = number of files sharing both tags.
    """
    data = load_tags()
    if not data:
        return {"nodes": [], "edges": [], "meta": {"mode": "tag", "node_count": 0, "edge_count": 0}}

    # Tag frequencies
    tag_freq: Counter = Counter()
    for tags in data.values():
        tag_freq.update(t.lower() for t in tags)

    # Co-occurrence counts
    pair_count: Counter = Counter()
    for tags in data.values():
        unique = list(set(t.lower() for t in tags))
        for a, b in itertools.combinations(sorted(unique), 2):
            pair_count[(a, b)] += 1

    # Cluster membership: tag → cluster_id (0-based index)
    cluster_result = find_tag_clusters(min_cluster_size=2)
    tag_to_cluster: Dict[str, int] = {}
    if cluster_result.get("success") and cluster_result.get("clusters"):
        for idx, (cluster_tag, _) in enumerate(cluster_result["clusters"].items()):
            tag_to_cluster[cluster_tag] = idx

    max_freq = max(tag_freq.values()) if tag_freq else 1

    # Inverted index: tag → list of file paths
    tag_to_files: Dict[str, List[str]] = defaultdict(list)
    for path, tags in data.items():
        for t in tags:
            tag_to_files[t.lower()].append(path)

    nodes: List[GraphNode] = []
    for tag, freq in tag_freq.items():
        group = tag_to_cluster.get(tag, len(_CLUSTER_COLORS) - 1)
        nodes.append(GraphNode(
            id=tag,
            label=tag,
            type="tag",
            size=_log_scale(freq, max_freq, 1.0, 8.0),
            color=_cluster_color(group),
            group=group,
            metadata={
                "file_count": freq,
                "cluster_id": group,
                "cluster_name": list(cluster_result.get("clusters", {}).keys())[group]
                if cluster_result.get("success") and group < len(cluster_result.get("clusters", {}))
                else None,
                "files": tag_to_files.get(tag, []),
            },
        ))

    edges: List[GraphEdge] = []
    for (a, b), weight in pair_count.items():
        if weight >= min_weight:
            edges.append(GraphEdge(
                source=a,
                target=b,
                weight=float(weight),
                directed=False,
                label=f"shared by {weight} file{'s' if weight != 1 else ''}",
            ))

    return {
        "nodes": [_node_dict(n) for n in nodes],
        "edges": [_edge_dict(e) for e in edges],
        "meta": {
            "mode": "tag",
            "node_count": len(nodes),
            "edge_count": len(edges),
            "total_files": len(data),
        },
    }


def build_file_graph(threshold: float = 0.2) -> dict:
    """
    Build a file similarity graph.
    Nodes = files, Edges = pairs with Jaccard similarity >= threshold.
    """
    data = load_tags()
    if not data:
        return {"nodes": [], "edges": [], "meta": {"mode": "file", "node_count": 0, "edge_count": 0}}

    files = list(data.keys())
    max_tags = max((len(v) for v in data.values()), default=1)

    nodes: List[GraphNode] = []
    for path in files:
        tags = data[path]
        ext = os.path.splitext(path)[1].lstrip(".").lower()
        color = _ext_color(path)
        is_dir = os.path.isdir(path)
        nodes.append(GraphNode(
            id=path,
            label=os.path.basename(path) or path,
            type="folder" if is_dir else "file",
            size=_log_scale(len(tags), max_tags, 1.0, 6.0),
            color=color,
            group=0,
            metadata={
                "path": path,
                "tags": tags,
                "extension": ext,
                "tag_count": len(tags),
            },
        ))

    # Build inverted index for efficient pair generation
    tag_to_files: Dict[str, List[str]] = defaultdict(list)
    for path, tags in data.items():
        for t in tags:
            tag_to_files[t.lower()].append(path)

    # Candidate pairs: files sharing at least one tag
    candidate_pairs: set = set()
    if len(files) <= 500:
        candidate_pairs = set(itertools.combinations(files, 2))
    else:
        for file_list in tag_to_files.values():
            for a, b in itertools.combinations(file_list, 2):
                if a > b:
                    a, b = b, a
                candidate_pairs.add((a, b))

    edges: List[GraphEdge] = []
    for a, b in candidate_pairs:
        tags_a = data.get(a, [])
        tags_b = data.get(b, [])
        sim = calculate_tag_similarity(tags_a, tags_b)
        if sim >= threshold:
            edges.append(GraphEdge(
                source=a,
                target=b,
                weight=round(sim, 4),
                directed=False,
                label=f"Jaccard {sim:.2f}",
            ))

    return {
        "nodes": [_node_dict(n) for n in nodes],
        "edges": [_edge_dict(e) for e in edges],
        "meta": {
            "mode": "file",
            "node_count": len(nodes),
            "edge_count": len(edges),
            "total_files": len(data),
            "threshold": threshold,
        },
    }


def build_mixed_graph(min_weight: int = 1) -> dict:
    """
    Build a bipartite graph: file nodes + tag nodes, directed file→tag edges.
    """
    data = load_tags()
    if not data:
        return {"nodes": [], "edges": [], "meta": {"mode": "mixed", "node_count": 0, "edge_count": 0}}

    tag_freq: Counter = Counter()
    for tags in data.values():
        tag_freq.update(t.lower() for t in tags)

    max_freq = max(tag_freq.values()) if tag_freq else 1
    max_tags_per_file = max((len(v) for v in data.values()), default=1)

    cluster_result = find_tag_clusters(min_cluster_size=2)
    tag_to_cluster: Dict[str, int] = {}
    if cluster_result.get("success"):
        for idx, cluster_tag in enumerate(cluster_result.get("clusters", {}).keys()):
            tag_to_cluster[cluster_tag] = idx

    nodes: List[GraphNode] = []
    seen_ids: set = set()

    # File/folder nodes
    for path, tags in data.items():
        node_id = f"file::{path}"
        is_dir = os.path.isdir(path)
        nodes.append(GraphNode(
            id=node_id,
            label=os.path.basename(path) or path,
            type="folder" if is_dir else "file",
            size=_log_scale(len(tags), max_tags_per_file, 1.0, 4.0),
            color=_ext_color(path),
            group=-1,
            metadata={
                "path": path,
                "tags": tags,
                "extension": os.path.splitext(path)[1].lstrip(".").lower(),
                "tag_count": len(tags),
            },
        ))
        seen_ids.add(node_id)

    # Tag nodes
    for tag, freq in tag_freq.items():
        node_id = f"tag::{tag}"
        group = tag_to_cluster.get(tag, len(_CLUSTER_COLORS) - 1)
        nodes.append(GraphNode(
            id=node_id,
            label=tag,
            type="tag",
            size=_log_scale(freq, max_freq, 1.0, 6.0),
            color=_cluster_color(group),
            group=group,
            metadata={
                "file_count": freq,
                "cluster_id": group,
            },
        ))
        seen_ids.add(node_id)

    edges: List[GraphEdge] = []
    for path, tags in data.items():
        file_id = f"file::{path}"
        for tag in tags:
            tag_id = f"tag::{tag.lower()}"
            edges.append(GraphEdge(
                source=file_id,
                target=tag_id,
                weight=1.0,
                directed=True,
                label=f"{os.path.basename(path)} → {tag}",
            ))

    return {
        "nodes": [_node_dict(n) for n in nodes],
        "edges": [_edge_dict(e) for e in edges],
        "meta": {
            "mode": "mixed",
            "node_count": len(nodes),
            "edge_count": len(edges),
            "total_files": len(data),
        },
    }


def get_all_extensions(graph_data: dict) -> List[str]:
    exts = set()
    for n in graph_data["nodes"]:
        ext = n.get("metadata", {}).get("extension", "")
        if ext:
            exts.add(ext)
    return sorted(exts)


def get_all_tags_in_graph(graph_data: dict) -> List[str]:
    tags = set()
    for n in graph_data["nodes"]:
        if n["type"] == "tag":
            tags.add(n["label"])
        else:
            for t in n.get("metadata", {}).get("tags", []):
                tags.add(t)
    return sorted(tags)


def get_cluster_names(graph_data: dict) -> List[Tuple[int, str]]:
    seen = {}
    for n in graph_data["nodes"]:
        g = n.get("group", -1)
        if g >= 0 and g not in seen:
            seen[g] = n["label"] if n["type"] == "tag" else f"Cluster {g}"
    return sorted(seen.items())
