"""Step 1 inventory: FakeNewsNet metadata CSVs.

Answers: how many articles, how many missing URLs/titles,
how rich is the propagation signal (tweets per article),
which domains dominate each label group.
"""
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd

DATA = Path(__file__).resolve().parents[1] / "data" / "raw" / "fakenewsnet"
FILES = ["politifact_fake", "politifact_real", "gossipcop_fake", "gossipcop_real"]


def domain_of(u: str) -> str:
    u = str(u).strip()
    if not u or u.lower() == "nan":
        return ""
    if not u.startswith(("http://", "https://")):
        u = "http://" + u
    net = urlparse(u).netloc.lower()
    return net[4:] if net.startswith("www.") else net


def main() -> None:
    summary = []
    for f in FILES:
        df = pd.read_csv(DATA / f"{f}.csv")
        dom = df["news_url"].apply(domain_of)
        tweets = (
            df["tweet_ids"].fillna("").astype(str)
            .apply(lambda s: len(s.split("\t")) if s else 0)
        )
        summary.append({
            "file": f,
            "articles": len(df),
            "missing_url": int(df["news_url"].isna().sum()),
            "missing_title": int(df["title"].isna().sum()),
            "median_tweets": float(tweets.median()),
            "p90_tweets": float(tweets.quantile(0.9)),
            "max_tweets": int(tweets.max()),
            "top_domains": dom.value_counts().head(3).to_dict(),
        })

    s = pd.DataFrame(summary)
    print(s[["file", "articles", "missing_url", "missing_title",
             "median_tweets", "p90_tweets", "max_tweets"]].to_string(index=False))
    print()
    for r in summary:
        print(f"{r['file']}: top domains = {r['top_domains']}")


if __name__ == "__main__":
    main()
