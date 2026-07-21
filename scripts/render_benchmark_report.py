"""
Render crawler benchmark JSON into Markdown and HTML reports.

Usage:
    python scripts/render_benchmark_report.py benchmark-results.json
"""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any


def pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def num(value: float) -> str:
    return f"{value:.2f}"


def get_metric(profile: dict[str, Any], path: list[str], default: float = 0.0) -> float:
    value: Any = profile
    for key in path:
        if not isinstance(value, dict):
            return default
        value = value.get(key, default)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def calculate_scores(profiles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    available_profiles = [profile for profile in profiles if profile.get("available")]
    max_throughput = max(
        (get_metric(profile, ["performance", "throughput_urls_per_second"]) for profile in available_profiles),
        default=0.0,
    )
    max_median = max(
        (get_metric(profile, ["performance", "median_ms"]) for profile in available_profiles),
        default=0.0,
    )

    rows = []
    for profile in profiles:
        throughput = get_metric(profile, ["performance", "throughput_urls_per_second"])
        median_ms = get_metric(profile, ["performance", "median_ms"])
        usable_rate = get_metric(profile, ["quality", "usable_rate"])
        recall = get_metric(profile, ["quality", "mean_required_recall"])
        noise = get_metric(profile, ["quality", "mean_noise_penalty"])
        text_f1 = get_metric(profile, ["quality", "mean_text_f1"])
        round_success_rate = get_metric(profile, ["reliability", "round_success_rate"])
        js_rate = get_metric(
            profile,
            ["capability", "by_tag", "javascript_required", "usable_rate"],
        )
        boilerplate_rate = get_metric(
            profile,
            ["capability", "by_tag", "boilerplate_removal", "usable_rate"],
        )
        speed_score = throughput / max_throughput if max_throughput else 0.0
        latency_score = 1 - (median_ms / max_median) if max_median else 0.0
        latency_score = max(latency_score, 0.0)
        quality_score = max(
            (usable_rate * 0.40)
            + (recall * 0.25)
            + (text_f1 * 0.25)
            + ((1 - noise) * 0.10),
            0.0,
        )
        capability_score = (js_rate * 0.45) + (boilerplate_rate * 0.25) + (usable_rate * 0.30)
        overall_score = (
            quality_score * 0.45
            + capability_score * 0.25
            + speed_score * 0.20
            + latency_score * 0.10
        )
        if not profile.get("available"):
            overall_score = 0.0

        rows.append(
            {
                "name": profile["name"],
                "available": bool(profile.get("available")),
                "positioning": profile.get("description", ""),
                "median_ms": median_ms,
                "throughput": throughput,
                "usable_rate": usable_rate,
                "recall": recall,
                "noise": noise,
                "text_f1": text_f1,
                "round_success_rate": round_success_rate,
                "js_rate": js_rate,
                "boilerplate_rate": boilerplate_rate,
                "quality_score": quality_score,
                "capability_score": capability_score,
                "speed_score": speed_score,
                "overall_score": overall_score,
                "profile": profile,
            }
        )
    return sorted(rows, key=lambda row: row["overall_score"], reverse=True)


def render_bar(value: float, max_value: float = 1.0) -> str:
    ratio = 0.0 if max_value <= 0 else min(max(value / max_value, 0.0), 1.0)
    return f'<div class="bar"><span style="width:{ratio * 100:.1f}%"></span></div>'


def render_markdown(report: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Crawler Benchmark Report",
        "",
        f"- Rounds: `{report.get('meta', {}).get('rounds', '-')}`",
        f"- URL count: `{report.get('meta', {}).get('url_count', '-')}`",
        f"- Preset: `{report.get('meta', {}).get('preset', '-')}`",
        f"- Profiles: `{', '.join(report.get('meta', {}).get('profiles', []))}`",
        "",
        "## Ranking",
        "",
        "| Rank | Profile | Overall | Usable | Recall | Text F1 | Rounds OK | JS | Boilerplate | Median ms | URLs/s |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for index, row in enumerate(rows, start=1):
        lines.append(
            "| "
            f"{index} | {row['name']} | {pct(row['overall_score'])} | "
            f"{pct(row['usable_rate'])} | {pct(row['recall'])} | {pct(row['text_f1'])} | "
            f"{pct(row['round_success_rate'])} | {pct(row['js_rate'])} | "
            f"{pct(row['boilerplate_rate'])} | {num(row['median_ms'])} | {num(row['throughput'])} |"
        )

    scenario_recommendations = report.get("scenario_recommendations", [])
    if scenario_recommendations:
        lines.extend(
            [
                "",
                "## Scenario Winners",
                "",
                "| Scenario | Use when | Best profile | Usable | Text F1 | Median ms |",
                "|---|---|---|---:|---:|---:|",
            ]
        )
        for item in scenario_recommendations:
            lines.append(
                "| "
                f"{item['scenario']} | {item['use_when']} | {item['best_profile']} | "
                f"{pct(item['best_usable_rate'])} | {pct(item['best_text_f1'])} | "
                f"{num(float(item['best_median_ms']))} |"
            )

    lines.extend(["", "## Notes", ""])
    lines.append(
        "- Overall score = quality 45% + capability 25% + throughput 20% + latency 10%; "
        "quality includes usable rate, snippet recall, token-level text F1, and noise penalty."
    )
    lines.append("- Required and forbidden snippets use exact-or-token matching to tolerate Markdown/browser formatting changes.")
    lines.append("- Real-world benchmark reports should be interpreted with network and site-change caveats.")
    lines.append("- Scenario winners exclude standalone stage probes such as `reader_service`; those remain in ranking as capability references.")
    lines.append("- `Rounds OK` shows profile-level reliability across benchmark rounds.")
    lines.append("- Unavailable profiles are scored as zero but retained for environment visibility.")
    lines.extend(
        [
            "",
            "## Metric Glossary",
            "",
            "| Metric | Meaning | How it is calculated |",
            "|---|---|---|",
            "| `success_rate` | Returned anything. | URLs with non-empty content / total URLs. This does not mean the content is high quality. |",
            "| `usable_rate` | Returned content good enough for downstream use. | Usable URLs / total URLs. A URL is usable when required snippet recall is at least 80%, no forbidden snippets are present, and normalized content length reaches the benchmark threshold. |",
            "| `mean_required_recall` | Expected gold content recall. | Average of required snippet hits / required snippets for each case. |",
            "| `mean_text_f1` | Word-level extraction quality. | Token overlap F1 between extracted content and the fixture ground-truth text. Higher is better. |",
            "| `mean_noise_penalty` | Boilerplate or noise leakage. | Average of forbidden snippet hits / forbidden snippets for each case. Lower is better. |",
            "| `javascript_required` | JavaScript-rendered page ability. | `usable_rate` among cases tagged `javascript_required`. |",
            "| `boilerplate_removal` | Template/noise removal ability. | `usable_rate` among cases tagged `boilerplate_removal`. |",
            "| `median_ms` | Typical end-to-end runtime. | Median profile runtime across benchmark rounds. Lower is better. |",
            "| `p95_ms` | Slow-tail runtime estimate. | 95th percentile profile runtime across rounds. Lower is better. |",
            "| `jitter_ms` | Runtime stability. | Max runtime minus min runtime across rounds. Lower is more stable. |",
            "| `throughput_urls_per_second` | Batch processing speed. | URL count / median runtime in seconds. Higher is better. |",
            "| `overall_score` | Ranking score in the rendered report. | Quality 45% + capability 25% + throughput 20% + latency 10%. This is a heuristic sorting score, not an absolute truth. |",
        ]
    )
    return "\n".join(lines) + "\n"


def render_html(report: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    max_throughput = max((row["throughput"] for row in rows), default=0.0)
    max_latency = max((row["median_ms"] for row in rows), default=0.0)
    recommendation_cards = "\n".join(render_profile_card(row, max_throughput, max_latency) for row in rows)
    scenario_recommendations = render_scenario_recommendations(report)
    capability_matrix = render_capability_matrix(rows)
    matrix = render_case_matrix(rows)
    raw_recommendations = html.escape(json.dumps(report.get("recommendations", []), indent=2, ensure_ascii=False))

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Crawler Benchmark Report</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f7f8fa;
      --panel: #ffffff;
      --text: #1f2933;
      --muted: #667085;
      --border: #d9dee7;
      --green: #168a55;
      --blue: #2463eb;
      --amber: #b7791f;
      --red: #c2410c;
    }}
    body {{
      margin: 0;
      font: 14px/1.5 system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--text);
      background: var(--bg);
    }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 28px; }}
    h1 {{ margin: 0 0 8px; font-size: 28px; }}
    h2 {{ margin: 28px 0 12px; font-size: 18px; }}
    .meta {{ color: var(--muted); margin-bottom: 20px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 14px; }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 14px;
      box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
    }}
    .card h3 {{ margin: 0 0 8px; font-size: 16px; display: flex; justify-content: space-between; gap: 8px; }}
    .score {{ font-variant-numeric: tabular-nums; color: var(--blue); }}
    .metric {{ display: grid; grid-template-columns: 120px 1fr 64px; align-items: center; gap: 8px; margin: 8px 0; }}
    .metric label {{ color: var(--muted); }}
    .bar {{ height: 8px; background: #edf1f7; border-radius: 999px; overflow: hidden; }}
    .bar span {{ display:block; height:100%; background: var(--blue); border-radius: inherit; }}
    .warn span {{ background: var(--amber); }}
    .good span {{ background: var(--green); }}
    .bad span {{ background: var(--red); }}
    table {{ width: 100%; border-collapse: collapse; background: var(--panel); border: 1px solid var(--border); }}
    th, td {{ padding: 9px 10px; border-bottom: 1px solid var(--border); text-align: left; }}
    th {{ background: #eef2f7; font-weight: 650; }}
    td.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
    .pill {{ padding: 2px 7px; border-radius: 999px; background: #edf1f7; color: var(--muted); font-size: 12px; }}
    .ok {{ color: var(--green); font-weight: 650; }}
    .no {{ color: var(--red); font-weight: 650; }}
    pre {{ overflow: auto; background: #111827; color: #d1d5db; padding: 12px; border-radius: 8px; }}
  </style>
</head>
<body>
<main>
  <h1>Crawler Benchmark Report</h1>
  <div class="meta">
    Rounds: <strong>{html.escape(str(report.get('meta', {}).get('rounds', '-')))}</strong> ·
    URLs: <strong>{html.escape(str(report.get('meta', {}).get('url_count', '-')))}</strong> ·
    Profiles: <strong>{html.escape(', '.join(report.get('meta', {}).get('profiles', [])))}</strong>
  </div>

  <h2>Profile Scorecards</h2>
  <section class="grid">{recommendation_cards}</section>

  <h2>Scenario Winners</h2>
  {scenario_recommendations}

  <h2>Capability Matrix</h2>
  {capability_matrix}

  <h2>Ranking Table</h2>
  {render_ranking_table(rows)}

  <h2>Metric Glossary</h2>
  {render_metric_glossary()}

  <h2>Case Matrix</h2>
  {matrix}

  <h2>Raw Recommendations</h2>
  <pre>{raw_recommendations}</pre>
</main>
</body>
</html>
"""


def render_profile_card(row: dict[str, Any], max_throughput: float, max_latency: float) -> str:
    available = '<span class="ok">available</span>' if row["available"] else '<span class="no">unavailable</span>'
    return f"""
    <article class="card">
      <h3>{html.escape(row['name'])} <span class="score">{pct(row['overall_score'])}</span></h3>
      <div class="meta">{available}</div>
      {metric('Overall', row['overall_score'], pct(row['overall_score']), 'good')}
      {metric('Usable', row['usable_rate'], pct(row['usable_rate']), 'good')}
      {metric('Recall', row['recall'], pct(row['recall']), 'good')}
      {metric('Text F1', row['text_f1'], pct(row['text_f1']), 'good')}
      {metric('Rounds OK', row['round_success_rate'], pct(row['round_success_rate']), 'good')}
      {metric('JS ability', row['js_rate'], pct(row['js_rate']), 'warn')}
      {metric('Boilerplate', row['boilerplate_rate'], pct(row['boilerplate_rate']), 'good')}
      {metric('Throughput', row['throughput'], f"{num(row['throughput'])} urls/s", '', max_throughput)}
      {metric('Latency', max_latency - row['median_ms'], f"{num(row['median_ms'])} ms", 'warn', max_latency)}
    </article>
    """


def metric(
    label: str,
    value: float,
    display: str,
    css_class: str = "",
    max_value: float = 1.0,
) -> str:
    return (
        f'<div class="metric {css_class}"><label>{html.escape(label)}</label>'
        f"{render_bar(value, max_value)}<span>{html.escape(display)}</span></div>"
    )


def render_ranking_table(rows: list[dict[str, Any]]) -> str:
    body = "\n".join(
        "<tr>"
        f"<td>{index}</td>"
        f"<td>{html.escape(row['name'])}</td>"
        f"<td class='num'>{pct(row['overall_score'])}</td>"
        f"<td class='num'>{pct(row['usable_rate'])}</td>"
        f"<td class='num'>{pct(row['recall'])}</td>"
        f"<td class='num'>{pct(row['text_f1'])}</td>"
        f"<td class='num'>{pct(row['round_success_rate'])}</td>"
        f"<td class='num'>{pct(row['js_rate'])}</td>"
        f"<td class='num'>{pct(row['boilerplate_rate'])}</td>"
        f"<td class='num'>{num(row['median_ms'])}</td>"
        f"<td class='num'>{num(row['throughput'])}</td>"
        "</tr>"
        for index, row in enumerate(rows, start=1)
    )
    return (
        "<table><thead><tr><th>#</th><th>Profile</th><th>Overall</th><th>Usable</th>"
        "<th>Recall</th><th>Text F1</th><th>Rounds OK</th><th>JS</th><th>Boilerplate</th><th>Median ms</th><th>URLs/s</th>"
        f"</tr></thead><tbody>{body}</tbody></table>"
    )


def render_scenario_recommendations(report: dict[str, Any]) -> str:
    recommendations = report.get("scenario_recommendations", [])
    if not recommendations:
        return '<p class="meta">No scenario recommendations were recorded.</p>'

    body = "\n".join(
        "<tr>"
        f"<td>{html.escape(item.get('scenario', '-'))}</td>"
        f"<td>{html.escape(item.get('use_when', '-'))}</td>"
        f"<td>{html.escape(item.get('best_profile', '-'))}</td>"
        f"<td class='num'>{pct(float(item.get('best_usable_rate', 0.0)))}</td>"
        f"<td class='num'>{pct(float(item.get('best_text_f1', 0.0)))}</td>"
        f"<td class='num'>{num(float(item.get('best_median_ms', 0.0)))}</td>"
        "</tr>"
        for item in recommendations
    )
    return (
        "<table><thead><tr><th>Scenario</th><th>Use when</th><th>Best profile</th>"
        "<th>Usable</th><th>Text F1</th><th>Median ms</th></tr></thead>"
        f"<tbody>{body}</tbody></table>"
    )


def render_capability_matrix(rows: list[dict[str, Any]]) -> str:
    tags = [
        "static_html",
        "article_extraction",
        "boilerplate_removal",
        "documentation_page",
        "structured_product_page",
        "multi_item_extraction",
        "javascript_required",
        "latency_tolerance",
    ]
    header = "".join(f"<th>{html.escape(tag)}</th>" for tag in tags)
    body_rows = []
    for row in rows:
        by_tag = row["profile"].get("capability", {}).get("by_tag", {})
        cells = []
        for tag in tags:
            stats = by_tag.get(tag)
            if not stats:
                cells.append("<td>-</td>")
                continue
            usable = float(stats.get("usable_rate", 0.0))
            text_f1 = float(stats.get("mean_text_f1", 0.0))
            css_class = "ok" if usable >= 0.8 else "no" if usable == 0 else ""
            cells.append(f"<td class='{css_class}'>{pct(usable)} / {pct(text_f1)}</td>")
        body_rows.append(f"<tr><th>{html.escape(row['name'])}</th>{''.join(cells)}</tr>")
    return (
        "<table><thead><tr><th>Profile</th>"
        f"{header}</tr></thead><tbody>{''.join(body_rows)}</tbody></table>"
    )


def render_metric_glossary() -> str:
    rows = [
        (
            "success_rate",
            "是否返回了内容",
            "有非空内容的 URL 数 / 总 URL 数。只说明抓到了东西，不代表内容质量好。",
        ),
        (
            "usable_rate",
            "是否足够可用",
            "可用 URL 数 / 总 URL 数。单个 URL 需要满足：required snippet 命中率 >= 80%、没有 forbidden snippet、正文长度达到阈值。",
        ),
        (
            "mean_required_recall",
            "黄金内容召回率",
            "每个 case 的 required snippet 命中数 / required snippet 总数，然后取平均。",
        ),
        (
            "mean_noise_penalty",
            "噪声泄漏率",
            "每个 case 的 forbidden snippet 命中数 / forbidden snippet 总数，然后取平均。越低越好。",
        ),
        (
            "javascript_required",
            "JS 页面能力",
            "只看带 javascript_required 标签的 case，在这些 case 上计算 usable_rate。",
        ),
        (
            "boilerplate_removal",
            "去模板噪声能力",
            "只看带 boilerplate_removal 标签的 case，在这些 case 上计算 usable_rate。",
        ),
        (
            "median_ms",
            "典型耗时",
            "多轮 benchmark 的端到端耗时中位数。越低越好。",
        ),
        (
            "p95_ms",
            "慢尾耗时",
            "多轮 benchmark 的 95 分位耗时。越低越好。",
        ),
        (
            "jitter_ms",
            "稳定性波动",
            "多轮 benchmark 最大耗时 - 最小耗时。越低说明越稳定。",
        ),
        (
            "throughput_urls_per_second",
            "吞吐",
            "URL 数 / median_ms 换算出的秒数。越高越好。",
        ),
        (
            "overall_score",
            "综合排序分",
            "quality 45% + capability 25% + throughput 20% + latency 10%。这是用于排序的启发式权重，不是绝对标准。",
        ),
    ]
    body = "\n".join(
        "<tr>"
        f"<td><code>{html.escape(name)}</code></td>"
        f"<td>{html.escape(meaning)}</td>"
        f"<td>{html.escape(calculation)}</td>"
        "</tr>"
        for name, meaning, calculation in rows
    )
    return (
        "<table><thead><tr><th>Metric</th><th>Meaning</th><th>Calculation</th></tr></thead>"
        f"<tbody>{body}</tbody></table>"
    )


def render_case_matrix(rows: list[dict[str, Any]]) -> str:
    case_ids = []
    for row in rows:
        for sample in row["profile"].get("samples", []):
            for case in sample.get("quality", {}).get("cases", []):
                if case["case_id"] not in case_ids:
                    case_ids.append(case["case_id"])

    header = "".join(f"<th>{html.escape(case_id)}</th>" for case_id in case_ids)
    body_rows = []
    for row in rows:
        cases = {}
        samples = row["profile"].get("samples", [])
        if samples:
            for case in samples[0].get("quality", {}).get("cases", []):
                cases[case["case_id"]] = case
        cells = []
        for case_id in case_ids:
            case = cases.get(case_id)
            if not case:
                cells.append("<td>-</td>")
                continue

            reasons = ", ".join(case.get("unusable_reasons", []))
            preview = case.get("content_preview", "")
            title = html.escape(" | ".join(part for part in (reasons, preview) if part))
            title_attr = f' title="{title}"' if title else ""
            if case.get("usable"):
                cells.append(f"<td class='ok'{title_attr}>usable</td>")
            elif case.get("found"):
                cells.append(f"<td class='no'{title_attr}>weak</td>")
            else:
                cells.append(f"<td class='no'{title_attr}>miss</td>")
        body_rows.append(f"<tr><th>{html.escape(row['name'])}</th>{''.join(cells)}</tr>")
    return f"<table><thead><tr><th>Profile</th>{header}</tr></thead><tbody>{''.join(body_rows)}</tbody></table>"


def render_metric_glossary() -> str:
    rows = [
        (
            "success_rate",
            "Returned anything",
            "URLs with non-empty content divided by total URLs. This does not imply quality.",
        ),
        (
            "usable_rate",
            "Returned usable content",
            "A case is usable when snippet recall is at least 80%, forbidden snippets are absent, and normalized length reaches the benchmark threshold.",
        ),
        (
            "mean_required_recall",
            "Gold snippet recall",
            "Average required snippet hits divided by required snippets for each case.",
        ),
        (
            "mean_text_f1",
            "Token-level content quality",
            "Token overlap F1 between extracted content and fixture ground-truth text.",
        ),
        (
            "mean_noise_penalty",
            "Boilerplate leakage",
            "Average forbidden snippet hits divided by forbidden snippets for each case. Lower is better.",
        ),
        (
            "javascript_required",
            "JavaScript-rendered page ability",
            "Usable rate among cases tagged javascript_required.",
        ),
        (
            "boilerplate_removal",
            "Template/noise removal ability",
            "Usable rate among cases tagged boilerplate_removal.",
        ),
        (
            "median_ms",
            "Typical runtime",
            "Median end-to-end runtime across benchmark rounds. Lower is better.",
        ),
        (
            "round_success_rate",
            "Profile reliability",
            "Benchmark rounds with at least one successful result divided by total rounds.",
        ),
        (
            "throughput_urls_per_second",
            "Batch throughput",
            "URL count divided by median runtime in seconds. Higher is better.",
        ),
        (
            "overall_score",
            "Heuristic ranking score",
            "Quality 45% + capability 25% + throughput 20% + latency 10%. Use scenario winners for final decisions.",
        ),
    ]
    body = "\n".join(
        "<tr>"
        f"<td><code>{html.escape(name)}</code></td>"
        f"<td>{html.escape(meaning)}</td>"
        f"<td>{html.escape(calculation)}</td>"
        "</tr>"
        for name, meaning, calculation in rows
    )
    return (
        "<table><thead><tr><th>Metric</th><th>Meaning</th><th>Calculation</th></tr></thead>"
        f"<tbody>{body}</tbody></table>"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="Benchmark JSON file")
    parser.add_argument("--html", type=Path, default=Path("benchmark-report.html"))
    parser.add_argument("--markdown", type=Path, default=Path("benchmark-report.md"))
    args = parser.parse_args()

    report = json.loads(args.input.read_text(encoding="utf-8"))
    rows = calculate_scores(report.get("profiles", []))
    args.markdown.write_text(render_markdown(report, rows), encoding="utf-8")
    args.html.write_text(render_html(report, rows), encoding="utf-8")
    print(f"Wrote {args.markdown}")
    print(f"Wrote {args.html}")


if __name__ == "__main__":
    main()
