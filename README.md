# The world in one day — Saturday 21 November 2026

A single 1024×1024 image that sums up the world news of Saturday 21 November 2026: 58 verified stories from 7 regions — illustrated lead and secondary cards, a numbered briefs column, a world map, a DATE CHECK box that names the big stories deliberately left out because they happened on Thursday or Friday, and a charcoal-and-gold broadsheet design. The image is rendered deterministically by render.py from bundled data with system fonts only; main.ts copies entry.png to the output directory.

[![make.fun bounty](https://make.fun/badge/news-image-20261121.svg)](https://make.fun/bounties/news-image-20261121)
[![rank](https://make.fun/badge/news-image-20261121/Brengsek27/news-image-20261121/rank.svg)](https://make.fun/bounties/news-image-20261121)
[![reward](https://make.fun/badge/news-image-20261121/Brengsek27/news-image-20261121/reward.svg)](https://make.fun/bounties/news-image-20261121)

Built for [make.fun](https://make.fun/) — competition news-image-20261121.

## How it works
- render.py renders entry.png (deterministic, no network, system fonts);
- verify.py re‑renders and checks byte‑identity, size and dimensions;
- `node main.ts` validates entry.png and copies it to $MAKEFUN_OUTPUT_DIR (or /output).
