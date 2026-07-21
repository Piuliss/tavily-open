# Crawler Benchmark Report

- Rounds: `2`
- URL count: `12`
- Preset: `fast`
- Profiles: `http_extractor, reader_service, scrapling_static, full_pipeline_reader`

## Ranking

| Rank | Profile | Overall | Usable | Recall | Text F1 | Rounds OK | JS | Boilerplate | Median ms | URLs/s |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | reader_service | 96.3% | 100.0% | 100.0% | 73.9% | 0.0% | 100.0% | 100.0% | 60.74 | 197.56 |
| 2 | full_pipeline_reader | 66.1% | 75.0% | 90.3% | 75.4% | 0.0% | 100.0% | 100.0% | 478.35 | 25.09 |
| 3 | http_extractor | 44.6% | 66.7% | 75.0% | 64.3% | 0.0% | 0.0% | 100.0% | 797.82 | 15.04 |
| 4 | scrapling_static | 32.5% | 16.7% | 83.3% | 70.5% | 0.0% | 0.0% | 0.0% | 333.65 | 35.97 |

## Scenario Winners

| Scenario | Use when | Best profile | Usable | Text F1 | Median ms |
|---|---|---|---:|---:|---:|
| static_html | mostly static HTML pages | http_extractor | 80.0% | 77.1% | 797.82 |
| article_extraction | articles and redirects | http_extractor | 100.0% | 100.0% | 797.82 |
| boilerplate_removal | navigation-heavy pages | http_extractor | 100.0% | 70.1% | 797.82 |
| documentation_page | developer documentation | http_extractor | 100.0% | 100.0% | 797.82 |
| structured_product_page | product detail pages | full_pipeline_reader | 100.0% | 71.2% | 478.35 |
| multi_item_extraction | listings and discussion threads | full_pipeline_reader | 75.0% | 78.2% | 478.35 |
| javascript_required | client-rendered shell pages | full_pipeline_reader | 100.0% | 71.4% | 478.35 |
| latency_tolerance | slow but valid static pages | scrapling_static | 100.0% | 100.0% | 333.65 |

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
