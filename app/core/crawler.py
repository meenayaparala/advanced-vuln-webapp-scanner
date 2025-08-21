import asyncio
import httpx
from urllib.parse import urljoin, urlsplit, urlunsplit
from bs4 import BeautifulSoup
from typing import Set, Tuple
from dataclasses import dataclass

@dataclass
class CrawlConfig:
    max_depth: int = 2
    same_domain_only: bool = True
    timeout: float = 10.0
    concurrency: int = 8

def normalize_url(base: str, href: str) -> str | None:
    if not href:
        return None
    abs_url = urljoin(base, href)
    parts = list(urlsplit(abs_url))
    parts[4] = ""  # fragment
    return urlunsplit(parts)

class AsyncCrawler:
    def __init__(self, start_url: str, db, project_id: int, log_cb=None, config: CrawlConfig = CrawlConfig()):
        self.start_url = start_url.rstrip("/")
        self.db = db
        self.project_id = project_id
        self.log = log_cb or (lambda s: None)
        self.cfg = config

        self.start_host = urlsplit(self.start_url).netloc
        self.visited: Set[str] = set()
        self.q: asyncio.Queue[Tuple[str, int]] = asyncio.Queue()

    def in_scope(self, url: str, depth: int) -> bool:
        if depth > self.cfg.max_depth:
            return False
        if self.cfg.same_domain_only:
            return urlsplit(url).netloc == self.start_host
        return True

    async def fetch(self, client: httpx.AsyncClient, url: str) -> httpx.Response | None:
        try:
            r = await client.get(url, timeout=self.cfg.timeout, follow_redirects=True)
            return r
        except Exception as e:
            self.log(f"[ERROR] GET {url} -> {e}")
            return None

    def parse_and_store(self, url: str, depth: int, response: httpx.Response):
        ctype = response.headers.get("content-type", "")
        status = response.status_code
        page_id = self.db.upsert_page(self.project_id, url, status, depth, ctype)

        if "html" not in ctype.lower():
            return []

        soup = BeautifulSoup(response.text, "html.parser")

        for form in soup.find_all("form"):
            action = form.get("action") or ""
            method = (form.get("method") or "GET").upper()
            abs_action = normalize_url(url, action) or url
            form_id = self.db.insert_form(page_id, abs_action, method)
            inputs = form.find_all(["input", "textarea", "select"])
            for inp in inputs:
                name = inp.get("name")
                type_ = inp.get("type") or inp.name
                value = inp.get("value")
                self.db.insert_input(form_id, name, type_, value)

        links = []
        for a in soup.find_all("a", href=True):
            nxt = normalize_url(url, a["href"])
            if nxt:
                links.append(nxt)
        return links

    async def worker(self, client: httpx.AsyncClient):
        while True:
            try:
                url, depth = await asyncio.wait_for(self.q.get(), timeout=0.5)
            except asyncio.TimeoutError:
                return
            if url in self.visited or not self.in_scope(url, depth):
                self.q.task_done()
                continue
            self.visited.add(url)
            self.log(f"[CRAWL] depth={depth} {url}")
            resp = await self.fetch(client, url)
            if resp is not None:
                new_links = self.parse_and_store(url, depth, resp)
                for nxt in new_links:
                    if nxt not in self.visited and self.in_scope(nxt, depth + 1):
                        await self.q.put((nxt, depth + 1))
            self.q.task_done()

    async def run(self):
        async with httpx.AsyncClient(headers={"User-Agent": "AVWAS/0.2"}) as client:
            await self.q.put((self.start_url, 0))
            tasks = [asyncio.create_task(self.worker(client)) for _ in range(self.cfg.concurrency)]
            await self.q.join()
            for t in tasks:
                t.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
        self.log(f"[DONE] Crawled {len(self.visited)} pages.")
