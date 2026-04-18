import json
from typing import Optional

from .service import get_all_extensions, get_all_tags_in_graph, get_cluster_names
from .export import to_gexf, to_graphml


def generate_html(
    graph_data: dict,
    start_3d: bool = False,
    server_port: Optional[int] = None,
    title: str = "Tag Network",
) -> str:
    mode = graph_data.get("meta", {}).get("mode", "tag")
    all_tags = get_all_tags_in_graph(graph_data)
    all_exts = get_all_extensions(graph_data)
    clusters = get_cluster_names(graph_data)
    gexf_content = to_gexf(graph_data)
    graphml_content = to_graphml(graph_data)

    graph_json = json.dumps(graph_data, ensure_ascii=False)
    gexf_json = json.dumps(gexf_content, ensure_ascii=False)
    graphml_json = json.dumps(graphml_content, ensure_ascii=False)
    server_port_js = str(server_port) if server_port else "null"
    start_3d_js = "true" if start_3d else "false"
    mode_js = json.dumps(mode)

    tag_options = "\n".join(
        f'<option value="{t}">{t}</option>' for t in all_tags
    )
    ext_options = "\n".join(
        f'<option value="{e}">.{e}</option>' for e in all_exts
    )
    cluster_options = '<option value="">All clusters</option>\n' + "\n".join(
        f'<option value="{cid}">Cluster {cid}: {cname}</option>'
        for cid, cname in clusters
    )

    meta = graph_data.get("meta", {})
    meta_info = (
        f"Mode: <b>{meta.get('mode','?')}</b> &nbsp;|&nbsp; "
        f"Nodes: <b>{meta.get('node_count',0)}</b> &nbsp;|&nbsp; "
        f"Edges: <b>{meta.get('edge_count',0)}</b> &nbsp;|&nbsp; "
        f"Files: <b>{meta.get('total_files',0)}</b>"
    )

    # Determine which filter sections are relevant
    show_ext_filter = "block" if mode in ("file", "mixed") else "none"
    show_tag_filter = "block" if mode in ("tag", "mixed") else "none"
    show_node_toggles = "block" if mode == "mixed" else "none"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>{title}</title>
<script src="https://unpkg.com/3d-force-graph@1.73.0/dist/3d-force-graph.min.js"></script>
<script src="https://unpkg.com/force-graph@1.43.0/dist/force-graph.min.js"></script>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: #0f1117; color: #e0e0e0; display: flex; height: 100vh; overflow: hidden; }}

  #sidebar {{
    width: 300px; min-width: 260px; max-width: 380px;
    background: #1a1d27; border-right: 1px solid #2e3147;
    display: flex; flex-direction: column; overflow: hidden;
    resize: horizontal;
  }}
  #sidebar-header {{
    padding: 14px 16px 10px; border-bottom: 1px solid #2e3147;
    background: #14162a;
  }}
  #sidebar-header h2 {{ font-size: 15px; color: #a0aec0; letter-spacing: .5px; margin-bottom: 4px; }}
  #meta-info {{ font-size: 11px; color: #667; line-height: 1.6; }}
  #meta-info b {{ color: #9ab; }}

  #sidebar-body {{ flex: 1; overflow-y: auto; padding: 12px; scrollbar-width: thin; }}
  #sidebar-body::-webkit-scrollbar {{ width: 5px; }}
  #sidebar-body::-webkit-scrollbar-thumb {{ background: #2e3147; border-radius: 3px; }}

  .section {{ margin-bottom: 14px; }}
  .section-title {{
    font-size: 10px; font-weight: 600; text-transform: uppercase;
    letter-spacing: .8px; color: #556; margin-bottom: 7px; padding-bottom: 4px;
    border-bottom: 1px solid #1e2133;
  }}

  label {{ font-size: 12px; color: #8899aa; display: block; margin-bottom: 3px; }}

  input[type=text], select {{
    width: 100%; padding: 6px 8px; background: #0f1117; border: 1px solid #2e3147;
    border-radius: 5px; color: #cdd; font-size: 12px; outline: none;
    transition: border-color .2s;
  }}
  input[type=text]:focus, select:focus {{ border-color: #4a6fa5; }}
  select[multiple] {{ height: 80px; }}

  .range-row {{ display: flex; align-items: center; gap: 8px; margin-top: 4px; }}
  .range-row input[type=range] {{ flex: 1; accent-color: #4a6fa5; }}
  .range-val {{ font-size: 11px; color: #667; min-width: 28px; text-align: right; }}

  .toggle-row {{ display: flex; align-items: center; gap: 8px; margin-bottom: 5px; }}
  .toggle-row input[type=checkbox] {{ accent-color: #4a6fa5; width: 14px; height: 14px; }}
  .toggle-row label {{ margin: 0; color: #8899aa; }}

  .btn {{
    display: inline-block; padding: 7px 12px; border-radius: 5px; font-size: 12px;
    cursor: pointer; border: none; font-weight: 600; letter-spacing: .3px;
    transition: background .2s, transform .1s;
  }}
  .btn:active {{ transform: scale(.97); }}
  .btn-primary {{ background: #2d4a7a; color: #c5d8f5; }}
  .btn-primary:hover {{ background: #3a5f9a; }}
  .btn-secondary {{ background: #1e2a1a; color: #8dbb6e; border: 1px solid #2a3a1f; }}
  .btn-secondary:hover {{ background: #263622; }}
  .btn-danger {{ background: #2a1a1a; color: #cc8888; border: 1px solid #3a1f1f; }}
  .btn-danger:hover {{ background: #3a2020; }}
  .btn-row {{ display: flex; gap: 6px; flex-wrap: wrap; margin-top: 6px; }}

  #graph-container {{ flex: 1; position: relative; background: #0a0b10; }}
  #graph-container canvas {{ display: block; }}

  #tooltip {{
    position: fixed; background: rgba(15,17,28,.95); border: 1px solid #2e3147;
    border-radius: 7px; padding: 10px 13px; font-size: 12px; line-height: 1.7;
    pointer-events: none; z-index: 1000; max-width: 280px; display: none;
    box-shadow: 0 4px 20px rgba(0,0,0,.5);
  }}
  #tooltip b {{ color: #a0c4ff; }}
  #tooltip .tag-badge {{
    display: inline-block; background: #1e2a3e; border: 1px solid #2e4060;
    border-radius: 3px; padding: 1px 6px; font-size: 10px; margin: 1px;
    color: #89b4d4;
  }}

  #status-bar {{
    position: absolute; bottom: 10px; left: 10px; font-size: 11px; color: #445;
    background: rgba(10,11,16,.7); padding: 4px 9px; border-radius: 4px;
    pointer-events: none;
  }}

  #copied-toast {{
    position: fixed; bottom: 30px; left: 50%; transform: translateX(-50%);
    background: #2a4a2a; color: #8dbb6e; padding: 8px 18px; border-radius: 6px;
    font-size: 13px; z-index: 9999; display: none; border: 1px solid #3a6a3a;
  }}

  .dim {{ opacity: 0.08 !important; }}
</style>
</head>
<body>

<div id="sidebar">
  <div id="sidebar-header">
    <h2>&#9651; Tag Network Visualizer</h2>
    <div id="meta-info">{meta_info}</div>
  </div>
  <div id="sidebar-body">

    <div class="section">
      <div class="section-title">View</div>
      <div class="btn-row">
        <button class="btn btn-primary" id="btn-toggle-dim" onclick="toggle3D()">Switch to 3D</button>
        <button class="btn btn-secondary" onclick="resetCamera()">Reset Camera</button>
      </div>
      <div style="margin-top:8px;">
        <label>Color by</label>
        <select id="color-by" onchange="applyFilters()">
          <option value="type">Node type</option>
          <option value="cluster">Cluster</option>
          <option value="filetype">File type</option>
        </select>
      </div>
      <div style="margin-top:6px;">
        <label>Highlight cluster</label>
        <select id="highlight-cluster" onchange="applyFilters()">
          {cluster_options}
        </select>
      </div>
    </div>

    <div class="section">
      <div class="section-title">Search</div>
      <input type="text" id="search" placeholder="Search nodes..." oninput="applyFilters()"/>
    </div>

    <div class="section" style="display:{show_ext_filter}" id="sec-ext">
      <div class="section-title">Filter by extension</div>
      <select id="ext-filter" multiple onchange="applyFilters()">
        {ext_options}
      </select>
      <div style="font-size:10px;color:#445;margin-top:3px;">Ctrl+click to multi-select</div>
    </div>

    <div class="section" style="display:{show_tag_filter}" id="sec-tags">
      <div class="section-title">Filter by tag</div>
      <select id="tag-filter" multiple onchange="applyFilters()">
        {tag_options}
      </select>
      <div style="font-size:10px;color:#445;margin-top:3px;">Ctrl+click to multi-select</div>
    </div>

    <div class="section">
      <div class="section-title">Edge weight</div>
      <label>Min weight: <span id="min-weight-val">1</span></label>
      <div class="range-row">
        <input type="range" id="min-weight" min="1" max="50" value="1" step="1" oninput="updateSliderLabel('min-weight','min-weight-val'); applyFilters()"/>
      </div>
    </div>

    <div class="section">
      <div class="section-title">Node degree</div>
      <label>Min degree: <span id="min-degree-val">0</span></label>
      <div class="range-row">
        <input type="range" id="min-degree" min="0" max="100" value="0" step="1" oninput="updateSliderLabel('min-degree','min-degree-val'); applyFilters()"/>
      </div>
      <label style="margin-top:6px;">Max degree: <span id="max-degree-val">∞</span></label>
      <div class="range-row">
        <input type="range" id="max-degree" min="0" max="100" value="100" step="1" oninput="updateSliderLabel('max-degree','max-degree-val',true); applyFilters()"/>
      </div>
    </div>

    <div class="section">
      <div class="section-title">Visibility</div>
      <div class="toggle-row">
        <input type="checkbox" id="show-isolated" onchange="applyFilters()"/>
        <label for="show-isolated">Show isolated nodes (degree 0)</label>
      </div>
      <div class="toggle-row" style="display:{show_node_toggles}" id="toggle-files">
        <input type="checkbox" id="show-files" checked onchange="applyFilters()"/>
        <label for="show-files">Show file/folder nodes</label>
      </div>
      <div class="toggle-row" style="display:{show_node_toggles}" id="toggle-tags">
        <input type="checkbox" id="show-tags-nodes" checked onchange="applyFilters()"/>
        <label for="show-tags-nodes">Show tag nodes</label>
      </div>
      <div class="toggle-row">
        <input type="checkbox" id="show-arrows" onchange="applyFilters()"/>
        <label for="show-arrows">Show directional arrows</label>
      </div>
    </div>

    <div class="section">
      <div class="section-title">Export</div>
      <div class="btn-row">
        <button class="btn btn-secondary" onclick="downloadGEXF()">&#8659; GEXF (Gephi)</button>
        <button class="btn btn-secondary" onclick="downloadGraphML()">&#8659; GraphML</button>
      </div>
    </div>

    <div class="section">
      <div class="section-title">Actions</div>
      <div class="btn-row">
        <button class="btn btn-danger" onclick="resetFilters()">Reset filters</button>
      </div>
    </div>

  </div>
</div>

<div id="graph-container"></div>
<div id="tooltip"></div>
<div id="status-bar">Drag to pan &nbsp;·&nbsp; Scroll to zoom &nbsp;·&nbsp; Click node to open</div>
<div id="copied-toast">Path copied to clipboard!</div>

<script>
const GRAPH_DATA = {graph_json};
const GEXF_DATA = {gexf_json};
const GRAPHML_DATA = {graphml_json};
const SERVER_PORT = {server_port_js};
const INITIAL_3D = {start_3d_js};
const GRAPH_MODE = {mode_js};

// ── color palettes ──────────────────────────────────────────────────────────
const CLUSTER_COLORS = [
  "#4e79a7","#f28e2b","#e15759","#76b7b2","#59a14f",
  "#edc948","#b07aa1","#ff9da7","#9c755f","#bab0ac",
  "#d37295","#fabfd2","#8cd17d","#b6992d","#f1ce63",
  "#499894","#86bcb6","#e15759","#79706e","#d4a6c8"
];
const TYPE_COLORS = {{ tag: "#4e79a7", file: "#59a14f", folder: "#f28e2b" }};
const EXT_COLORS = {{
  py:"#3572A5",js:"#f1e05a",ts:"#2b7489",tsx:"#2b7489",jsx:"#f1e05a",
  html:"#e34c26",css:"#563d7c",json:"#292929",md:"#083fa1",txt:"#89e051",
  pdf:"#b30b00",png:"#a97bff",jpg:"#a97bff",jpeg:"#a97bff",gif:"#a97bff",
  svg:"#ff9900",sh:"#89e051",bat:"#C1F12E",rs:"#dea584",go:"#00ADD8",
  java:"#b07219",c:"#555555",cpp:"#f34b7d",rb:"#701516",php:"#4F5D95",
  swift:"#ffac45",kt:"#F18E33",cs:"#178600",yml:"#cb171e",yaml:"#cb171e",
  toml:"#9c4221",xml:"#0060ac",csv:"#237346",xlsx:"#217346",
  zip:"#999999",tar:"#999999",gz:"#999999",sql:"#e38c00",db:"#e38c00"
}};

// ── state ────────────────────────────────────────────────────────────────────
let graph = null;
let use3D = INITIAL_3D;

function getNodeColor(n, colorBy) {{
  if (colorBy === "cluster") {{
    return CLUSTER_COLORS[n.group % CLUSTER_COLORS.length] || "#888";
  }} else if (colorBy === "filetype") {{
    const ext = (n.metadata && n.metadata.extension) || "";
    return EXT_COLORS[ext] || "#888888";
  }}
  return TYPE_COLORS[n.type] || n.color || "#888";
}}

function computeDegrees(edges) {{
  const deg = {{}};
  for (const e of edges) {{
    deg[e.source] = (deg[e.source] || 0) + 1;
    deg[e.target] = (deg[e.target] || 0) + 1;
  }}
  return deg;
}}

function currentFilteredData() {{
  const search = document.getElementById("search").value.toLowerCase().trim();
  const minWeight = parseFloat(document.getElementById("min-weight").value);
  const minDeg = parseInt(document.getElementById("min-degree").value);
  const maxDegRaw = parseInt(document.getElementById("max-degree").value);
  const maxDeg = maxDegRaw >= 100 ? Infinity : maxDegRaw;
  const showIsolated = document.getElementById("show-isolated").checked;
  const showArrows = document.getElementById("show-arrows").checked;
  const colorBy = document.getElementById("color-by").value;
  const highlightCluster = document.getElementById("highlight-cluster").value;

  const extFilter = Array.from(document.getElementById("ext-filter").selectedOptions).map(o => o.value);
  const tagFilter = Array.from(document.getElementById("tag-filter").selectedOptions).map(o => o.value);

  const showFiles = document.getElementById("show-files") ? document.getElementById("show-files").checked : true;
  const showTagNodes = document.getElementById("show-tags-nodes") ? document.getElementById("show-tags-nodes").checked : true;

  // Pre-filter edges by weight
  const validEdges = GRAPH_DATA.edges.filter(e => e.weight >= minWeight);
  const degs = computeDegrees(validEdges);

  // Filter nodes
  const visibleIds = new Set();
  for (const n of GRAPH_DATA.nodes) {{
    if (GRAPH_MODE === "mixed") {{
      if (n.type !== "tag" && !showFiles) continue;
      if (n.type === "tag" && !showTagNodes) continue;
    }}
    const deg = degs[n.id] || 0;
    if (!showIsolated && deg === 0) continue;
    if (deg < minDeg || deg > maxDeg) continue;
    if (search && !n.label.toLowerCase().includes(search)) continue;
    if (extFilter.length > 0 && n.type !== "tag") {{
      const ext = (n.metadata && n.metadata.extension) || "";
      if (!extFilter.includes(ext)) continue;
    }}
    if (tagFilter.length > 0) {{
      if (n.type === "tag") {{
        if (!tagFilter.includes(n.label)) continue;
      }} else {{
        const nodeTags = (n.metadata && n.metadata.tags) || [];
        if (!nodeTags.some(t => tagFilter.includes(t))) continue;
      }}
    }}
    visibleIds.add(n.id);
  }}

  const filteredEdges = validEdges.filter(e => visibleIds.has(e.source) && visibleIds.has(e.target));

  const filteredNodes = GRAPH_DATA.nodes
    .filter(n => visibleIds.has(n.id))
    .map(n => {{
      let color = getNodeColor(n, colorBy);
      if (highlightCluster && String(n.group) !== highlightCluster) {{
        color = color + "28"; // ~15% opacity
      }}
      return {{ ...n, color }};
    }});

  const links = filteredEdges.map(e => ({{
    ...e,
    __directed: showArrows && e.directed
  }}));

  return {{ nodes: filteredNodes, links }};
}}

function applyFilters() {{
  if (!graph) return;
  const data = currentFilteredData();
  graph.graphData(data);
}}

function initGraph() {{
  const container = document.getElementById("graph-container");
  container.innerHTML = "";
  const data = currentFilteredData();
  const showArrows = document.getElementById("show-arrows").checked;

  const Ctor = use3D ? ForceGraph3D : ForceGraph;
  graph = Ctor()(container)
    .graphData(data)
    .nodeId("id")
    .nodeLabel(n => buildTooltip(n))
    .nodeVal(n => n.size * n.size)
    .nodeColor(n => n.color)
    .linkSource("source")
    .linkTarget("target")
    .linkWidth(l => Math.max(0.4, Math.log1p(l.weight) * 0.9))
    .linkLabel(l => l.label)
    .linkColor(() => "rgba(100,120,160,0.35)")
    .linkDirectionalArrowLength(l => (l.__directed || showArrows) ? 4 : 0)
    .linkDirectionalArrowRelPos(1)
    .onNodeClick(handleNodeClick)
    .onNodeHover(handleNodeHover);

  if (use3D) {{
    graph
      .linkOpacity(0.5)
      .nodeThreeObject(n => {{
        const sprite = new SpriteText(n.label);
        sprite.color = n.color;
        sprite.textHeight = Math.max(2, n.size * 1.2);
        return sprite;
      }});
  }} else {{
    graph
      .nodeCanvasObject((n, ctx, globalScale) => {{
        const label = n.label;
        const fontSize = Math.max(8, 11 / globalScale);
        const r = Math.max(2, n.size * 2.5);
        ctx.beginPath();
        ctx.arc(n.x, n.y, r, 0, 2 * Math.PI, false);
        ctx.fillStyle = n.color || "#4e79a7";
        ctx.fill();
        if (globalScale > 0.6) {{
          ctx.font = `${{fontSize}}px Segoe UI,sans-serif`;
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.fillStyle = "rgba(255,255,255,0.85)";
          ctx.fillText(label.length > 20 ? label.slice(0,18) + "…" : label, n.x, n.y + r + fontSize * 0.7);
        }}
      }})
      .nodeCanvasObjectMode(() => "replace");
  }}

  document.getElementById("btn-toggle-dim").textContent = use3D ? "Switch to 2D" : "Switch to 3D";
}}

function toggle3D() {{
  use3D = !use3D;
  initGraph();
}}

function resetCamera() {{
  if (graph && graph.zoomToFit) graph.zoomToFit(400);
  if (graph && graph.cameraPosition) graph.cameraPosition({{ x: 0, y: 0, z: 200 }}, {{ x:0,y:0,z:0 }}, 600);
}}

// ── tooltips ─────────────────────────────────────────────────────────────────
function buildTooltip(n) {{
  if (n.type === "tag") {{
    const fc = (n.metadata && n.metadata.file_count) || 0;
    const cl = (n.metadata && n.metadata.cluster_id != null) ? n.metadata.cluster_id : "–";
    return `<b>${{n.label}}</b><br>Type: tag<br>Files: ${{fc}}<br>Cluster: ${{cl}}`;
  }}
  const tags = (n.metadata && n.metadata.tags) || [];
  const path = (n.metadata && n.metadata.path) || n.id;
  const tagBadges = tags.slice(0, 12).map(t => `<span class="tag-badge">${{t}}</span>`).join(" ");
  const more = tags.length > 12 ? `<br><small>+${{tags.length - 12}} more</small>` : "";
  return `<b>${{n.label}}</b><br>Type: ${{n.type}}<br>Path: <small>${{path}}</small><br>${{tagBadges}}${{more}}`;
}}

const tooltip = document.getElementById("tooltip");
function handleNodeHover(n) {{
  if (n) {{
    tooltip.innerHTML = buildTooltip(n);
    tooltip.style.display = "block";
  }} else {{
    tooltip.style.display = "none";
  }}
}}
document.addEventListener("mousemove", e => {{
  tooltip.style.left = (e.clientX + 14) + "px";
  tooltip.style.top = (e.clientY - 10) + "px";
}});

// ── click to open ─────────────────────────────────────────────────────────────
function handleNodeClick(n) {{
  const path = (n.metadata && n.metadata.path) || (n.type !== "tag" ? n.id.replace(/^file::/, "") : null);
  if (!path) return;
  if (SERVER_PORT) {{
    fetch("http://127.0.0.1:" + SERVER_PORT + "/open?path=" + encodeURIComponent(path))
      .catch(() => copyPath(path));
  }} else {{
    copyPath(path);
  }}
}}

function copyPath(path) {{
  navigator.clipboard.writeText(path).catch(() => {{}});
  const toast = document.getElementById("copied-toast");
  toast.style.display = "block";
  setTimeout(() => {{ toast.style.display = "none"; }}, 2000);
}}

// ── exports ───────────────────────────────────────────────────────────────────
function downloadBlob(content, filename, mime) {{
  const blob = new Blob([content], {{ type: mime }});
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
  URL.revokeObjectURL(a.href);
}}

function downloadGEXF() {{ downloadBlob(GEXF_DATA, "tag_network.gexf", "application/xml"); }}
function downloadGraphML() {{ downloadBlob(GRAPHML_DATA, "tag_network.graphml", "application/xml"); }}

// ── slider labels ─────────────────────────────────────────────────────────────
function updateSliderLabel(sliderId, labelId, isMax) {{
  const val = document.getElementById(sliderId).value;
  document.getElementById(labelId).textContent = (isMax && parseInt(val) >= 100) ? "∞" : val;
}}

// ── reset filters ─────────────────────────────────────────────────────────────
function resetFilters() {{
  document.getElementById("search").value = "";
  document.getElementById("min-weight").value = 1;
  document.getElementById("min-degree").value = 0;
  document.getElementById("max-degree").value = 100;
  document.getElementById("min-weight-val").textContent = "1";
  document.getElementById("min-degree-val").textContent = "0";
  document.getElementById("max-degree-val").textContent = "∞";
  document.getElementById("show-isolated").checked = false;
  document.getElementById("show-arrows").checked = false;
  document.getElementById("color-by").value = "type";
  document.getElementById("highlight-cluster").value = "";
  const extSel = document.getElementById("ext-filter");
  if (extSel) Array.from(extSel.options).forEach(o => o.selected = false);
  const tagSel = document.getElementById("tag-filter");
  if (tagSel) Array.from(tagSel.options).forEach(o => o.selected = false);
  const sf = document.getElementById("show-files");
  if (sf) sf.checked = true;
  const st = document.getElementById("show-tags-nodes");
  if (st) st.checked = true;
  applyFilters();
}}

// ── SpriteText shim for 3D labels (loaded lazily) ────────────────────────────
let SpriteText = class {{
  constructor(text) {{
    this.text = text;
    this.color = "#fff";
    this.textHeight = 8;
    // minimal three.js object stub so it doesn't crash when 3D lib tries to add it
    this.position = {{ set() {{}} }};
    this.scale = {{ set() {{}} }};
  }}
}};
// Try to load the real SpriteText
(function() {{
  const s = document.createElement("script");
  s.src = "https://unpkg.com/three-spritetext@1.6.5/dist/three-spritetext.min.js";
  s.onload = () => {{ if (window.SpriteText) SpriteText = window.SpriteText; }};
  document.head.appendChild(s);
}})();

// ── init ──────────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {{
  initGraph();
  // Dynamically set max values for sliders based on actual data
  const allEdgeWeights = GRAPH_DATA.edges.map(e => e.weight);
  if (allEdgeWeights.length) {{
    const maxW = Math.ceil(Math.max(...allEdgeWeights));
    document.getElementById("min-weight").max = maxW;
  }}
  const allDegrees = Object.values((() => {{
    const d = {{}};
    for (const e of GRAPH_DATA.edges) {{
      d[e.source] = (d[e.source]||0)+1;
      d[e.target] = (d[e.target]||0)+1;
    }}
    return d;
  }})());
  if (allDegrees.length) {{
    const maxD = Math.max(...allDegrees);
    document.getElementById("min-degree").max = maxD;
    document.getElementById("max-degree").max = maxD;
    document.getElementById("max-degree").value = maxD;
  }}
}});
</script>
</body>
</html>"""
