#!/usr/bin/env python3
"""Resolve every image in apps/<app>/images.txt to the digest its tag points at today and
write apps/<app>/images.lock (laptop only; anonymous registry API calls, no credentials).

Columns: ref, resolved digest, linux/amd64 present, and for Docker Hub tags the date the tag
was last pushed. A tag last pushed before the thesis run date still points at the image the
thesis ran. Refs that already carry a digest are checked against what their tag says now.
Usage: python3 apps/tools/resolve_images.py [app ...]
"""
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

APPS_DIR = Path(__file__).resolve().parents[1]
RUN_DATES = {"boutique": "2026-09-03", "bank": "2026-09-04", "dsb": "2026-09-04", "otel": "2026-09-06",
             "teastore": "2026-09-06"}
ACCEPT = ", ".join([
    "application/vnd.oci.image.index.v1+json", "application/vnd.docker.distribution.manifest.list.v2+json",
    "application/vnd.oci.image.manifest.v1+json", "application/vnd.docker.distribution.manifest.v2+json"])
_tokens = {}


def parse(ref):
    digest = None
    if "@" in ref:
        ref, digest = ref.split("@", 1)
    first = ref.split("/", 1)[0]
    if "/" in ref and ("." in first or ":" in first or first == "localhost"):
        registry, repo = ref.split("/", 1)
    else:
        registry, repo = "docker.io", ref
    if registry == "docker.io" and "/" not in repo:
        repo = "library/" + repo
    tag = None
    if ":" in repo.rsplit("/", 1)[-1]:
        repo, tag = repo.rsplit(":", 1)
    if tag is None and digest is None:
        tag = "latest"
    return registry, repo, tag, digest


def api(registry):
    return "https://registry-1.docker.io" if registry == "docker.io" else f"https://{registry}"


def request(registry, repo, path, method="GET", accept=ACCEPT):
    url = f"{api(registry)}/v2/{repo}/{path}"
    for _ in range(2):
        req = urllib.request.Request(url, method=method, headers={"Accept": accept})
        if (registry, repo) in _tokens:
            req.add_header("Authorization", f"Bearer {_tokens[(registry, repo)]}")
        try:
            return urllib.request.urlopen(req, timeout=30)
        except urllib.error.HTTPError as e:
            if e.code != 401 or (registry, repo) in _tokens:
                raise
            h = e.headers.get("WWW-Authenticate", "")
            p = dict(re.findall(r'(\w+)="([^"]*)"', h))
            q = f"{p['realm']}?service={p.get('service', '')}&scope=repository:{repo}:pull"
            with urllib.request.urlopen(q, timeout=30) as r:
                d = json.load(r)
            _tokens[(registry, repo)] = d.get("token") or d.get("access_token")
    raise RuntimeError("auth loop")


def has_amd64(registry, repo, digest):
    with request(registry, repo, f"manifests/{digest}") as r:
        m = json.load(r)
    if "manifests" in m:
        return any(x.get("platform", {}).get("architecture") == "amd64" for x in m["manifests"])
    with request(registry, repo, f"blobs/{m['config']['digest']}", accept="*/*") as r:
        return json.load(r).get("architecture") == "amd64"


def hub_pushed(repo, tag):
    try:
        with urllib.request.urlopen(f"https://hub.docker.com/v2/repositories/{repo}/tags/{tag}", timeout=30) as r:
            d = json.load(r)
        return (d.get("tag_last_pushed") or d.get("last_updated") or "")[:10]
    except Exception:
        return "?"


def resolve(app):
    lines = [f"# {app}: images.txt resolved {__import__('datetime').date.today()} (thesis run {RUN_DATES[app]})",
             "# ref\tdigest the tag points at now\tamd64\tnote"]
    for ref in (APPS_DIR / app / "images.txt").read_text().split():
        registry, repo, tag, pinned = parse(ref)
        note = []
        try:
            now = None
            if tag:
                with request(registry, repo, f"manifests/{tag}", method="HEAD") as r:
                    now = r.headers["Docker-Content-Digest"]
            digest = pinned or now
            if pinned and now and pinned != now:
                note.append(f"tag {tag} now points at {now}; the pinned digest is used")
            amd = "yes" if has_amd64(registry, repo, digest) else "NO"
            if registry == "docker.io" and tag and not pinned:
                pushed = hub_pushed(repo, tag)
                if pushed and pushed != "?":
                    rel = "before" if pushed < RUN_DATES[app] else "AFTER"
                    note.append(f"tag last pushed {pushed}, {rel} the thesis run")
            lines.append(f"{ref}\t{digest}\t{amd}\t{'; '.join(note)}")
        except Exception as e:  # keep going; the line says what failed
            lines.append(f"{ref}\t?\t?\tresolve failed: {e}")
    (APPS_DIR / app / "images.lock").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    for a in sys.argv[1:] or list(RUN_DATES):
        resolve(a)
