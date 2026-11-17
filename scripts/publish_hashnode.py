import glob
import os
import re
import sys
import requests
import yaml

HASHNODE_API = "https://gql.hashnode.com"
TOKEN = os.environ.get("HASHNODE_TOKEN", "").strip()
PUB_ID = os.environ.get("HASHNODE_PUBLICATION_ID", "").strip()

if not TOKEN or not PUB_ID:
    print("Error: HASHNODE_TOKEN or HASHNODE_PUBLICATION_ID is missing.")
    sys.exit(1)

HEADERS = {
    "Authorization": TOKEN,
    "Content-Type": "application/json",
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (compatible; HashnodeSync/1.0)",
}


def gql_request(query: str, variables: dict) -> dict:
    resp = requests.post(
        HASHNODE_API,
        json={"query": query, "variables": variables},
        headers=HEADERS,
        timeout=30,
    )
    if not resp.ok or not resp.text.strip():
        raise RuntimeError(
            f"HTTP {resp.status_code} | Empty or error response: {resp.text[:500]}"
        )
    try:
        data = resp.json()
    except ValueError as exc:
        raise RuntimeError(
            f"Invalid JSON (HTTP {resp.status_code}): {resp.text[:500]}"
        ) from exc

    if "errors" in data:
        raise RuntimeError(f"GraphQL Error: {data['errors']}")
    return data["data"]

def get_existing_posts() -> dict:
    """获取当前博客已发布的文章列表，返回 {slug: post_id} 映射"""
    query = """
    query GetPosts($pubId: ObjectId!) {
      publication(id: $pubId) {
        posts(first: 50) {
          edges {
            node {
              id
              slug
            }
          }
        }
      }
    }
    """
    data = gql_request(query, {"pubId": PUB_ID})
    edges = data.get("publication", {}).get("posts", {}).get("edges", [])
    return {edge["node"]["slug"]: edge["node"]["id"] for edge in edges}


def parse_markdown(filepath: str):
    with open(filepath, "r", encoding="utf-8") as f:
        raw = f.read()

    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", raw, re.DOTALL)
    if not match:
        return None, raw

    meta = yaml.safe_load(match.group(1)) or {}
    body = match.group(2).strip()
    return meta, body


def format_tags(raw_tags) -> list:
    if not raw_tags:
        return []
    if isinstance(raw_tags, str):
        tag_list = [t.strip() for t in raw_tags.split(",") if t.strip()]
    else:
        tag_list = [str(t).strip() for t in raw_tags if str(t).strip()]

    formatted = []
    for t in tag_list:
        slug = re.sub(r"[^a-z0-9-]", "", t.lower().replace(" ", "-"))
        if slug:
            formatted.append({"slug": slug, "name": t})
    return formatted


def sync_post(filepath: str, existing_posts: dict):
    meta, body = parse_markdown(filepath)
    if not meta or not meta.get("title"):
        print(f"Skipping {filepath}: missing YAML frontmatter or 'title'.")
        return

    if meta.get("published") is False:
        print(f"Skipping {filepath}: 'published' is set to false.")
        return

    default_slug = os.path.splitext(os.path.basename(filepath))[0].lower()
    slug = meta.get("slug", default_slug)
    title = meta["title"]
    tags = format_tags(meta.get("tags"))
    cover = meta.get("cover")

    post_input = {
        "title": title,
        "contentMarkdown": body,
        "slug": slug,
        "tags": tags,
    }
    if cover:
        post_input["coverImageOptions"] = {"coverImageURL": cover}

    if slug in existing_posts:
        post_input["id"] = existing_posts[slug]
        mutation = """
        mutation UpdatePost($input: UpdatePostInput!) {
          updatePost(input: $input) {
            post { id slug url }
          }
        }
        """
        res = gql_request(mutation, {"input": post_input})
        url = res["updatePost"]["post"]["url"]
        print(f"Updated: {title} -> {url}")
    else:
        post_input["publicationId"] = PUB_ID
        mutation = """
        mutation PublishPost($input: PublishPostInput!) {
          publishPost(input: $input) {
            post { id slug url }
          }
        }
        """
        res = gql_request(mutation, {"input": post_input})
        url = res["publishPost"]["post"]["url"]
        print(f"Published: {title} -> {url}")


def main():
    md_files = sorted(glob.glob("hashnode/**/*.md", recursive=True))
    if not md_files:
        print("No markdown files found in hashnode/ directory.")
        return

    existing_posts = get_existing_posts()
    for filepath in md_files:
        sync_post(filepath, existing_posts)


if __name__ == "__main__":
    main()