# Crawler Benchmark Report

- Rounds: `1`
- URL count: `12`
- Preset: `fast`
- Profiles: `scrapling_dynamic`

## Ranking

| Rank | Profile | Overall | Usable | Recall | Text F1 | Rounds OK | JS | Boilerplate | Median ms | URLs/s |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | scrapling_dynamic | 46.2% | 16.7% | 100.0% | 84.8% | 0.0% | 0.0% | 0.0% | 37135.11 | 0.32 |

## Scenario Winners

| Scenario | Use when | Best profile | Usable | Text F1 | Median ms |
|---|---|---|---:|---:|---:|
| static_html | mostly static HTML pages | scrapling_dynamic | 20.0% | 84.6% | 37135.11 |
| article_extraction | articles and redirects | scrapling_dynamic | 0.0% | 86.5% | 37135.11 |
| boilerplate_removal | navigation-heavy pages | scrapling_dynamic | 0.0% | 30.2% | 37135.11 |
| documentation_page | developer documentation | scrapling_dynamic | 0.0% | 88.6% | 37135.11 |
| structured_product_page | product detail pages | scrapling_dynamic | 0.0% | 88.9% | 37135.11 |
| multi_item_extraction | listings and discussion threads | scrapling_dynamic | 0.0% | 89.2% | 37135.11 |
| javascript_required | client-rendered shell pages | scrapling_dynamic | 0.0% | 85.7% | 37135.11 |
| latency_tolerance | slow but valid static pages | scrapling_dynamic | 100.0% | 100.0% | 37135.11 |

## Notes

- Overall score = quality 45% + capability 25% + throughput 20% + latency 10%; quality includes usable rate, snippet recall, token-level text F1, and noise penalty.
- Required and forbidden snippets use exact-or-token matching to tolerate Markdown/browser formatting changes.
- Real-world benchmark reports should be interpreted with network and site-change caveats.
- Scenario winners exclude standalone stage probes such as `reader_service`; those remain in ranking as capability references.
- `Rounds OK` shows profile-level reliability across benchmark rounds.
- Unavailable profiles are scored as zero but retained for environment visibility.

## Metric Glossary

| Metric | Meaning | How it is calculated |
|---|---|---|
| `success_rate` | Returned anything. | URLs with non-empty content / total URLs. This does not mean the content is high quality. |
| `usable_rate` | Returned content good enough for downstream use. | Usable URLs / total URLs. A URL is usable when required snippet recall is at least 80%, no forbidden snippets are present, and normalized content length reaches the benchmark threshold. |
| `mean_required_recall` | Expected gold content recall. | Average of required snippet hits / required snippets for each case. |
| `mean_text_f1` | Word-level extraction quality. | Token overlap F1 between extracted content and the fixture ground-truth text. Higher is better. |
| `mean_noise_penalty` | Boilerplate or noise leakage. | Average of forbidden snippet hits / forbidden snippets for each case. Lower is better. |
| `javascript_required` | JavaScript-rendered page ability. | `usable_rate` among cases tagged `javascript_required`. |
| `boilerplate_removal` | Template/noise removal ability. | `usable_rate` among cases tagged `boilerplate_removal`. |
| `median_ms` | Typical end-to-end runtime. | Median profile runtime across benchmark rounds. Lower is better. |
| `p95_ms` | Slow-tail runtime estimate. | 95th percentile profile runtime across rounds. Lower is better. |
| `jitter_ms` | Runtime stability. | Max runtime minus min runtime across rounds. Lower is more stable. |
| `throughput_urls_per_second` | Batch processing speed. | URL count / median runtime in seconds. Higher is better. |
| `overall_score` | Ranking score in the rendered report. | Quality 45% + capability 25% + throughput 20% + latency 10%. This is a heuristic sorting score, not an absolute truth. |
