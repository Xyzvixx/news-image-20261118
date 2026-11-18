# The World in One Day — 18 November 2026

[![news-image-20261118](https://make.fun/badge/news-image-20261118.svg)](https://make.fun/bounty/news-image-20261118)
[![rank](https://make.fun/badge/news-image-20261118/Xyzvixx/news-image-20261118/rank.svg)](https://make.fun/bounty/news-image-20261118)
[![reward](https://make.fun/badge/news-image-20261118/Xyzvixx/news-image-20261118/reward.svg)](https://make.fun/bounty/news-image-20261118)

One image that sums up the world's news of **Wednesday, 18 November 2026**,
drawn as a newspaper front page. `main.py` (Python 3.13, standard library
only, no network) copies `entry.png` to `/output/entry.png`, verifying first
that it is a whole PNG within the limits (1024×1024, under 1 MiB). Two runs
write byte-identical output.

![The World in One Day — 18 November 2026](entry.png)

## The day's news in the image

| Story | What the image says |
|---|---|
| Trump lands in Manila for Quad talks | US president in the Philippines ahead of a visit to China |
| Ukraine hits Crimea bridge again | Second day of strikes; Russia hits bridges in Kyiv |
| Iran drones target US radar in Bahrain | Gulf states on alert overnight |
| Nvidia posts record $115.8bn revenue | Sales up 103%; CEO spy-link probe |
| UK & Australia sanction settlement firms | West Bank building targeted |
| Dhoni calls time on IPL career | Retires as a player; becomes Chennai Super Kings mentor |
| Also today | Aid access urged for flooded Gaza; Cyclone Akvan strengthens; Amazon pledges $7bn for renewables in India; cyberattack hits supermarkets in 7 nations |

Headlines were checked against wire reports published on 18 November 2026.
The pictures are flat editorial illustrations made for this entry — not
photographs of the events — as the footer of the image itself says.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
# writes out/entry.png (457,953 bytes, 1024x1024)
```

## License

MIT — see [LICENSE](LICENSE).
