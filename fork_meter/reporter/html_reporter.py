"""
HTML reporter for fork-meter complexity analysis.

Produces a self-contained, interactive HTML file with a sortable complexity table.

:author: Ron Webb
:since: 1.0.0
"""

import logging
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment

from .. import __version__
from ..analyzer import AnalysisResult

_logger = logging.getLogger(__name__)

_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>fork-meter — Complexity Report</title>
  <style>
    :root {
      --bg: #e8eaed; --surface: #f0f2f5; --overlay: #dde0e6;
      --text: #2c2f3a; --subtext: #5a6070; --accent: #5b21b6;
      --border: #c4c8d0;
      --green: #16a34a; --yellow: #d97706; --orange: #ea580c; --red: #dc2626;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: var(--bg); color: var(--text);
      font-family: 'Segoe UI', system-ui, sans-serif; padding: 2rem;
    }
    h1 { color: var(--accent); font-size: 1.6rem; margin-bottom: 0.25rem; }
    .meta { color: var(--subtext); font-size: 0.8rem; margin-bottom: 1.75rem; }
    .summary { display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 1.75rem; }
    .card {
      background: var(--surface); border: 1px solid var(--border);
      border-radius: 8px; padding: 1rem 1.5rem; min-width: 140px;
    }
    .card .label {
      color: var(--subtext); font-size: 0.7rem;
      text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.35rem;
    }
    .card .value { font-size: 2rem; font-weight: 700; color: var(--accent); }
    .empty { color: var(--green); margin-top: 2rem; }
    table { width: 100%; border-collapse: collapse; background: var(--surface); border-radius: 8px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,.08); }
    thead { background: var(--overlay); }
    th {
      padding: 0.75rem 1rem; text-align: left; color: var(--subtext);
      font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.06em;
      cursor: pointer; user-select: none; white-space: nowrap;
    }
    th:hover { color: var(--text); }
    th.sort-asc::after  { content: ' ↑'; color: var(--accent); }
    th.sort-desc::after { content: ' ↓'; color: var(--accent); }
    td { padding: 0.6rem 1rem; border-top: 1px solid var(--border); font-size: 0.875rem; }
    tr:hover td { background: var(--overlay); }
    .file { color: var(--subtext); font-size: 0.8rem; word-break: break-all; }
    .name { font-weight: 600; }
    .tag {
      display: inline-block; padding: 0.15rem 0.5rem; border-radius: 4px;
      font-size: 0.7rem; background: var(--overlay); color: var(--subtext);
    }
    .cc { font-weight: 700; font-size: 1rem; }
    .cc-low  { color: var(--green);  }
    .cc-med  { color: var(--yellow); }
    .cc-high { color: var(--orange); }
    .cc-crit { color: var(--red);    }
  </style>
</head>
<body>
  <h1>fork-meter</h1>
  <p class="meta">
    Generated {{ generated_at }}&nbsp;&middot;&nbsp;
    fork-meter v{{ version }}&nbsp;&middot;&nbsp;
    Threshold: complexity &gt; {{ max_threshold }}
  </p>
  <div class="summary">
    <div class="card">
      <div class="label">Files Scanned</div>
      <div class="value">{{ files_scanned }}</div>
    </div>
    <div class="card">
      <div class="label">Functions Analyzed</div>
      <div class="value">{{ functions_analyzed }}</div>
    </div>
    <div class="card">
      <div class="label">Above Threshold</div>
      <div class="value">{{ results | length }}</div>
    </div>
  </div>
  {% if results %}
  <table id="tbl">
    <thead>
      <tr>
        <th data-col="0">File</th>
        <th data-col="1">Class</th>
        <th data-col="2">Code Block</th>
        <th data-col="3">Type</th>
        <th data-col="4">Lines</th>
        <th data-col="5">Complexity</th>
      </tr>
    </thead>
    <tbody>
      {% for r in results %}
      <tr>
        <td class="file">{{ r.file_path }}</td>
        <td>{{ r.parent_class if r.parent_class else '\u2014' }}</td>
        <td class="name">{{ r.name }}</td>
        <td><span class="tag">{{ r.fragment_type }}</span></td>
        <td>{{ r.line_count }}</td>
        <td class="cc {% if r.complexity <= 5 %}cc-low
                      {%- elif r.complexity <= 10 %}cc-med
                      {%- elif r.complexity <= 15 %}cc-high
                      {%- else %}cc-crit{% endif %}">{{ r.complexity }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  {% else %}
  <p class="empty">&#10003; No functions exceed the complexity threshold of {{ max_threshold }}.</p>
  {% endif %}
  <script>
    (function () {
      var tbl = document.getElementById('tbl');
      if (!tbl) { return; }
      var sc = 5, sd = -1;
      function sortBy(col) {
        if (sc === col) { sd *= -1; } else { sc = col; sd = (col >= 4) ? -1 : 1; }
        var tb = tbl.querySelector('tbody');
        var rows = Array.prototype.slice.call(tb.rows);
        rows.sort(function (a, b) {
          var av = a.cells[col].textContent.trim();
          var bv = b.cells[col].textContent.trim();
          if (col >= 4) { return (parseInt(av, 10) - parseInt(bv, 10)) * sd; }
          return av.localeCompare(bv) * sd;
        });
        rows.forEach(function (r) { tb.appendChild(r); });
        tbl.querySelectorAll('th').forEach(function (th, i) {
          th.classList.remove('sort-asc', 'sort-desc');
          if (i === sc) { th.classList.add(sd === 1 ? 'sort-asc' : 'sort-desc'); }
        });
      }
      tbl.querySelectorAll('th').forEach(function (th) {
        th.addEventListener('click', function () { sortBy(parseInt(th.dataset.col, 10)); });
      });
      sortBy(5);
    }());
  </script>
</body>
</html>"""


def write(result: AnalysisResult, max_threshold: int, output_path: Path) -> Path:
    """Render the complexity report as a self-contained HTML file.

    :param result: Aggregated analysis output.
    :param max_threshold: Complexity threshold used for filtering.
    :param output_path: Destination ``.html`` file path.
    :returns: Resolved path of the written file.
    """
    env = Environment(autoescape=True)
    template = env.from_string(_TEMPLATE)
    html = template.render(
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        version=__version__,
        max_threshold=max_threshold,
        files_scanned=result.files_scanned,
        functions_analyzed=result.functions_analyzed,
        results=result.results,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    _logger.info("HTML report written to %s", output_path)
    return output_path.resolve()
