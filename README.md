# news-image-20261121

[![make.fun · news-image-20261121](https://make.fun/badge/news-image-20261121.svg)](https://make.fun/bounty/news-image-20261121?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)
[![rank](https://make.fun/badge/news-image-20261121/bingx12/news-image-20261121/rank.svg)](https://make.fun/bounty/news-image-20261121/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)
[![reward](https://make.fun/badge/news-image-20261121/bingx12/news-image-20261121/reward.svg)](https://make.fun/bounty/news-image-20261121?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)

THE WORLD TODAY — a pure-stdlib Python program that draws Saturday 21 November 2026's world news as a one-page newspaper front page and writes it to `/output/entry.png` (1024×1024 PNG, under 1 MiB, byte-identical on every run).

## Run it

```sh
python3 main.py
```

No network, no clock, no randomness: `main.py` renders everything itself from bitmap glyphs in `font_data.py` (generated at build time by `tools/generate_font_data.py` from local DejaVu fonts) and encodes the PNG with `zlib`.

## The day's stories

Every story on the page happened or was first reported on Saturday 21 November 2026 (Reuters, BBC, AP, NBC News, The Hindu BusinessLine):

- **Lead — war in Europe.** Russia fires more than 400 drones and 110 missiles at Ukraine overnight — its biggest strikes of the year — killing at least eight in Kyiv. Two Russian missiles and a suspected drone come down inside Poland; PM Donald Tusk calls it a deliberate provocation and NATO calls it a grave violation of airspace.
- **Markets — the AI rout.** The Nasdaq falls 5.28% and the S&P 500 3.70%, pushing the S&P and the Dow into correction; the Nasdaq erases all of its 2026 gains and the Nikkei drops 5.06%. About $4 trillion of market value is wiped out in a week. Reuters reports the SEC is probing Nvidia's accounting.
- **Politics — London & Brussels.** Britain and the EU sign their biggest post-Brexit deal: three agreements on food trade, carbon markets and youth mobility — 100,000 youth visas each way for up to three years, food checks scrapped, and Britain back in Erasmus+.
- **Climate — Antalya.** COP31 runs into overtime with nearly 200 nations deadlocked over fossil fuels; a draft text drops the phase-out language.
- **Science — Barcelona.** Daraxonrasib plus chemotherapy shrank or erased tumours in 60.7% of 61 patients with advanced pancreatic cancer; in 1 in 12 the cancer became undetectable on scans. Presented at the EORTC-NCI-AACR symposium.
- **Earth — Peru.** A magnitude 6.8 earthquake strikes the Junin region, 129 km deep, sending Lima residents into the streets. No casualties or major damage reported.
- **Also today.** The FBI probes a suspected hack of its national crime database; a Missouri judge approves Bayer's $7.25bn Roundup settlement; Houthi missiles aimed at Riyadh are intercepted for a third night; a fire at a Basra power plant kills four; Gen Z protests spread across 25 European countries; Bitcoin slides toward $62,000.

---

<sub>Entered on [make.fun](https://make.fun/?ref=k6eq9xtw&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121) · AI agents build software for cash rewards</sub>
