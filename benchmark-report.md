# Crawler Benchmark Report

- Rounds: `1`
- URL count: `6`
- Profiles: `local_playwright, scrapling_static, scrapling_dynamic`

## Ranking

| Rank | Profile | Overall | Usable | Recall | JS | Boilerplate | Median ms | URLs/s |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | scrapling_static | 47.0% | 16.7% | 66.7% | 0.0% | 0.0% | 621.43 | 9.66 |
| 2 | local_playwright | 14.8% | 16.7% | 16.7% | 0.0% | 0.0% | 5341.88 | 1.12 |
| 3 | scrapling_dynamic | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 10068.59 | 0.60 |

## Notes

- Overall score = quality 45% + capability 25% + throughput 20% + latency 10%.
- Real-world benchmark reports should be interpreted with network and site-change caveats.
- Unavailable profiles are scored as zero but retained for environment visibility.

## Metric Glossary

| Metric | Meaning | How it is calculated |
|---|---|---|
| `success_rate` | Returned anything. | URLs with non-empty content / total URLs. This does not mean the content is high quality. |
| `usable_rate` | Returned content good enough for downstream use. | Usable URLs / total URLs. A URL is usable when required snippet recall is at least 80%, no forbidden snippets are present, and normalized content length reaches the benchmark threshold. |
| `mean_required_recall` | Expected gold content recall. | Average of required snippet hits / required snippets for each case. |
| `mean_noise_penalty` | Boilerplate or noise leakage. | Average of forbidden snippet hits / forbidden snippets for each case. Lower is better. |
| `javascript_required` | JavaScript-rendered page ability. | `usable_rate` among cases tagged `javascript_required`. |
| `boilerplate_removal` | Template/noise removal ability. | `usable_rate` among cases tagged `boilerplate_removal`. |
| `median_ms` | Typical end-to-end runtime. | Median profile runtime across benchmark rounds. Lower is better. |
| `p95_ms` | Slow-tail runtime estimate. | 95th percentile profile runtime across rounds. Lower is better. |
| `jitter_ms` | Runtime stability. | Max runtime minus min runtime across rounds. Lower is more stable. |
| `throughput_urls_per_second` | Batch processing speed. | URL count / median runtime in seconds. Higher is better. |
| `overall_score` | Ranking score in the rendered report. | Quality 45% + capability 25% + throughput 20% + latency 10%. This is a heuristic sorting score, not an absolute truth. |
