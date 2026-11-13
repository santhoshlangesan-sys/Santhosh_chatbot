import asyncio
from datetime import datetime, timezone
from pathlib import Path

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig


# URL = "https://www.cricinfo.com/records"
URL = "https://www.cricinfo.com/records/most-runs-in-career-83548"
OUTPUT_PATH = Path(__file__).with_name("MostRuns-records.md")


async def crawl_records() -> None:
    async with AsyncWebCrawler(
        config=BrowserConfig(headless=True, verbose=False)
    ) as crawler:
        result = await crawler.arun(
            url=URL,
            config=CrawlerRunConfig(
                page_timeout=90_000,
                wait_until="domcontentloaded",
            ),
        )

    if not result.success:
        raise RuntimeError(result.error_message or f"Failed to crawl {URL}")

    markdown = (
        result.markdown.raw_markdown
        if hasattr(result.markdown, "raw_markdown")
        else str(result.markdown or "")
    )
    if not markdown.strip():
        raise RuntimeError(f"Crawl returned no Markdown content for {URL}")

    title = result.metadata.get("title") if result.metadata else "Cricket Records"
    crawled_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    document = (
        f"# {title}\n\n"
        f"Source: {result.url}\n\n"
        f"Crawled at: {crawled_at}\n\n"
        f"{markdown.rstrip()}\n"
    )
    OUTPUT_PATH.write_text(document, encoding="utf-8")
    print(f"Saved Markdown to {OUTPUT_PATH}")


if __name__ == "__main__":
    asyncio.run(crawl_records())
