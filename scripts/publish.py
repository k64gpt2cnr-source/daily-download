#!/usr/bin/env python3
"""
Daily Download — publish an episode and regenerate the RSS feed.

Usage:
    python3 scripts/publish.py --date 2026-07-27 \
        --mp3 /tmp/pod/Daily_Download_2026-07-27.mp3 \
        --desc-file /tmp/pod/recap.txt

Run from the repo root. Adds the MP3 to episodes/, records metadata in
episodes.json, prunes to KEEP_EPISODES, and rewrites feed.xml.
Committing and pushing is done by the caller.
"""
import argparse, json, os, sys
from email.utils import format_datetime
from datetime import datetime, timezone, timedelta
from xml.sax.saxutils import escape

BASE = "https://raw.githubusercontent.com/k64gpt2cnr-source/daily-download/main"
KEEP_EPISODES = 14
TITLE = "Daily Download"
AUTHOR = "Daily Download"
DESCRIPTION = ("A daily news brief for Nishi. Real estate first, then world news, "
               "markets, entertainment, football and local NJ/NY. Roughly fifteen minutes, "
               "read by a British host.")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def mp3_meta(path):
    from mutagen.mp3 import MP3
    info = MP3(path).info
    secs = int(info.length)
    return secs, os.path.getsize(path)


def hms(secs):
    return f"{secs // 3600:02d}:{(secs % 3600) // 60:02d}:{secs % 60:02d}"


def load_index():
    p = os.path.join(ROOT, "episodes.json")
    if os.path.exists(p):
        with open(p) as f:
            return json.load(f)
    return []


def save_index(eps):
    with open(os.path.join(ROOT, "episodes.json"), "w") as f:
        json.dump(eps, f, indent=2)


def build_feed(eps):
    now = datetime.now(timezone.utc)
    items = []
    for e in eps:
        # 6:00 AM America/New_York == 10:00 UTC (EDT). Close enough for ordering.
        pub = datetime.fromisoformat(e["date"]).replace(
            hour=10, minute=0, tzinfo=timezone.utc)
        url = f"{BASE}/episodes/{e['date']}.mp3"
        items.append(f"""    <item>
      <title>{escape(e['title'])}</title>
      <description>{escape(e['description'])}</description>
      <itunes:summary>{escape(e['description'])}</itunes:summary>
      <pubDate>{format_datetime(pub)}</pubDate>
      <guid isPermaLink="false">daily-download-{e['date']}</guid>
      <enclosure url="{url}" length="{e['bytes']}" type="audio/mpeg"/>
      <itunes:duration>{hms(e['seconds'])}</itunes:duration>
      <itunes:episodeType>full</itunes:episodeType>
      <itunes:explicit>false</itunes:explicit>
    </item>""")

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
     xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"
     xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>{TITLE}</title>
    <link>{BASE}/</link>
    <description>{escape(DESCRIPTION)}</description>
    <language>en-us</language>
    <lastBuildDate>{format_datetime(now)}</lastBuildDate>
    <itunes:author>{AUTHOR}</itunes:author>
    <itunes:summary>{escape(DESCRIPTION)}</itunes:summary>
    <itunes:type>episodic</itunes:type>
    <itunes:explicit>false</itunes:explicit>
    <itunes:image href="{BASE}/cover.jpg"/>
    <image>
      <url>{BASE}/cover.jpg</url>
      <title>{TITLE}</title>
      <link>{BASE}/</link>
    </image>
    <itunes:category text="News">
      <itunes:category text="Business News"/>
    </itunes:category>
    <itunes:owner>
      <itunes:name>{AUTHOR}</itunes:name>
      <itunes:email>kambhaladinne.nishitha@gmail.com</itunes:email>
    </itunes:owner>
{chr(10).join(items)}
  </channel>
</rss>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--mp3", required=True)
    ap.add_argument("--desc-file", help="plain-text episode description")
    ap.add_argument("--desc", default="")
    args = ap.parse_args()

    desc = args.desc
    if args.desc_file:
        desc = open(args.desc_file).read().strip()
    if not desc:
        desc = "Today's brief."

    os.makedirs(os.path.join(ROOT, "episodes"), exist_ok=True)
    dest = os.path.join(ROOT, "episodes", f"{args.date}.mp3")
    if os.path.abspath(args.mp3) != os.path.abspath(dest):
        with open(args.mp3, "rb") as s, open(dest, "wb") as d:
            d.write(s.read())

    secs, size = mp3_meta(dest)
    pretty = datetime.fromisoformat(args.date).strftime("%A, %B %-d, %Y")

    eps = [e for e in load_index() if e["date"] != args.date]
    eps.append({
        "date": args.date,
        "title": f"{pretty}",
        "description": desc,
        "seconds": secs,
        "bytes": size,
    })
    eps.sort(key=lambda e: e["date"], reverse=True)

    # prune
    for old in eps[KEEP_EPISODES:]:
        p = os.path.join(ROOT, "episodes", f"{old['date']}.mp3")
        if os.path.exists(p):
            os.remove(p)
            print(f"pruned {old['date']}")
    eps = eps[:KEEP_EPISODES]

    save_index(eps)
    with open(os.path.join(ROOT, "feed.xml"), "w") as f:
        f.write(build_feed(eps))

    print(f"published {args.date}  {hms(secs)}  {size/1e6:.1f} MB  ({len(eps)} in feed)")


if __name__ == "__main__":
    main()
