#!/usr/bin/env python3
"""
GEO Fix — Check and generate missing files for GEO optimization.

Checks if the target website is missing:
- llms.txt
- robots.txt (or has issues)
- JSON-LD schema (Organization, WebSite, FAQPage, etc.)

Creates ./<domain>/ directory and generates missing files.

Usage:
    python geo_fix.py <url> [--check-only]
"""

import sys
import json
import os
import re
from datetime import datetime
from urllib.parse import urlparse

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("ERROR: Required packages not installed. Run: pip install -r requirements.txt")
    sys.exit(1)

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def get_domain_dir(url: str) -> str:
    """Get directory name for the domain."""
    parsed = urlparse(url)
    domain = parsed.netloc.replace(":", "_")
    return domain


def check_llms_txt(url: str) -> dict:
    """Check if llms.txt exists."""
    parsed = urlparse(url)
    llms_url = f"{parsed.scheme}://{parsed.netloc}/llms.txt"

    result = {"exists": False, "url": llms_url, "content": ""}
    try:
        response = requests.get(llms_url, headers=DEFAULT_HEADERS, timeout=15)
        if response.status_code == 200:
            result["exists"] = True
            result["content"] = response.text
    except:
        pass
    return result


def check_robots_txt(url: str) -> dict:
    """Check if robots.txt exists and has AI crawler rules."""
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    result = {
        "exists": False,
        "url": robots_url,
        "content": "",
        "has_ai_rules": False,
        "ai_crawlers_blocked": [],
        "ai_crawlers_allowed": [],
    }

    try:
        response = requests.get(robots_url, headers=DEFAULT_HEADERS, timeout=15)
        if response.status_code == 200:
            result["exists"] = True
            result["content"] = response.text

            # Check for AI crawler rules
            ai_crawlers = ["GPTBot", "ClaudeBot", "PerplexityBot", "Google-Extended", "OAI-SearchBot", "CCBot"]
            content_lower = response.text.lower()

            for crawler in ai_crawlers:
                if crawler.lower() in content_lower:
                    # Check if blocked
                    lines = response.text.split("\n")
                    blocked = False
                    for line in lines:
                        if line.lower().startswith(f"user-agent: {crawler.lower()}"):
                            blocked = True
                        elif line.lower().startswith("user-agent:") and not line.lower().startswith(f"user-agent: {crawler.lower()}"):
                            blocked = False
                        elif blocked and line.lower().startswith("disallow:"):
                            if line.lower().contains("/"):
                                result["ai_crawlers_blocked"].append(crawler)
                                break

            if result["ai_crawlers_blocked"]:
                result["has_ai_rules"] = True

    except:
        pass
    return result


def check_json_ld(url: str) -> dict:
    """Check existing JSON-LD schemas on the homepage."""
    result = {
        "found": [],
        "missing": [],
        "issues": [],
    }

    try:
        response = requests.get(url, headers=DEFAULT_HEADERS, timeout=30)
        soup = BeautifulSoup(response.text, "lxml")

        schemas = soup.find_all("script", type="application/ld+json")
        for schema in schemas:
            try:
                data = json.loads(schema.string)
                if isinstance(data, dict):
                    schema_type = data.get("@type", "")
                    if isinstance(schema_type, list):
                        schema_type = ", ".join(schema_type)
                    result["found"].append(schema_type)
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            schema_type = item.get("@type", "")
                            if isinstance(schema_type, list):
                                schema_type = ", ".join(schema_type)
                            result["found"].append(schema_type)
            except:
                result["issues"].append("Invalid JSON-LD detected")

    except Exception as e:
        result["issues"].append(f"Error fetching page: {str(e)}")

    return result


def generate_llms_txt(url: str, max_pages: int = 30) -> str:
    """Generate llms.txt content."""
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    # Fetch homepage
    try:
        response = requests.get(url, headers=DEFAULT_HEADERS, timeout=30)
        soup = BeautifulSoup(response.text, "lxml")
    except Exception as e:
        return f"# {parsed.netloc}\n> Error fetching site: {str(e)}\n"

    # Extract site name and description
    title = soup.find("title")
    site_name = title.get_text(strip=True).split("|")[0].split("-")[0].strip() if title else parsed.netloc
    meta_desc = soup.find("meta", attrs={"name": "description"})
    site_description = meta_desc.get("content", "") if meta_desc else f"Official website of {site_name}"

    # Discover and categorize pages
    pages = {
        "Main Pages": [],
        "Products & Services": [],
        "Resources & Blog": [],
        "Company": [],
        "Support": [],
    }

    seen_urls = set()
    for link in soup.find_all("a", href=True):
        href = urljoin(base_url, link["href"])
        link_text = link.get_text(strip=True)

        if not link_text or len(link_text) < 2:
            continue

        parsed_href = urlparse(href)
        if parsed_href.netloc != parsed.netloc:
            continue
        if href in seen_urls:
            continue
        if any(ext in href for ext in [".pdf", ".jpg", ".png", ".gif", ".css", ".js"]):
            continue

        seen_urls.add(href)
        path = parsed_href.path.lower()

        page_entry = {"url": href, "title": link_text}

        if any(kw in path for kw in ["/pricing", "/feature", "/product", "/solution", "/demo"]):
            pages["Products & Services"].append(page_entry)
        elif any(kw in path for kw in ["/blog", "/article", "/resource", "/guide", "/learn", "/docs", "/documentation"]):
            pages["Resources & Blog"].append(page_entry)
        elif any(kw in path for kw in ["/about", "/team", "/career", "/contact", "/press", "/partner"]):
            pages["Company"].append(page_entry)
        elif any(kw in path for kw in ["/help", "/support", "/faq", "/status"]):
            pages["Support"].append(page_entry)
        elif path in ["/", ""] or any(kw in path for kw in ["/home", "/index"]):
            if href != base_url and href != base_url + "/":
                pages["Main Pages"].append(page_entry)
        else:
            pages["Main Pages"].append(page_entry)

        if len(seen_urls) >= max_pages:
            break

    # Generate llms.txt
    lines = [f"# {site_name}", f"> {site_description}", ""]

    for section, section_pages in pages.items():
        if section_pages:
            lines.append(f"## {section}")
            for page in section_pages[:10]:
                lines.append(f"- [{page['title']}]({page['url']})")
            lines.append("")

    lines.extend([
        "## Contact",
        f"- Website: {base_url}",
        f"- Email: contact@{parsed.netloc}",
        "",
    ])

    return "\n".join(lines)


def generate_robots_txt(url: str) -> str:
    """Generate robots.txt with AI crawler rules."""
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    # Fetch existing robots.txt to preserve rules
    existing_content = ""
    try:
        response = requests.get(f"{base_url}/robots.txt", headers=DEFAULT_HEADERS, timeout=15)
        if response.status_code == 200:
            existing_content = response.text
    except:
        pass

    # Build new robots.txt with AI crawler rules
    lines = [
        "# robots.txt - Generated by GEO-SEO Analysis Tool",
        f"# Date: {datetime.now().strftime('%Y-%m-%d')}",
        "",
        "User-agent: *",
        "Allow: /",
        "",
        "# AI Crawlers - Allow all",
        "User-agent: GPTBot",
        "Allow: /",
        "",
        "User-agent: OAI-SearchBot",
        "Allow: /",
        "",
        "User-agent: ClaudeBot",
        "Allow: /",
        "",
        "User-agent: PerplexityBot",
        "Allow: /",
        "",
        "User-agent: Google-Extended",
        "Allow: /",
        "",
        "User-agent: CCBot",
        "Allow: /",
        "",
        "# Sitemap",
        f"Sitemap: {base_url}/sitemap.xml",
        "",
    ]

    return "\n".join(lines)


def generate_schema_jsonld(url: str, brand_name: str = "") -> str:
    """Generate JSON-LD schema files for Organization, WebSite, FAQPage."""
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    domain = parsed.netloc

    if not brand_name:
        brand_name = domain.split(".")[0].title()

    # Fetch homepage for meta
    try:
        response = requests.get(url, headers=DEFAULT_HEADERS, timeout=30)
        soup = BeautifulSoup(response.text, "lxml")
        title = soup.find("title")
        title_text = title.get_text(strip=True) if title else brand_name
        meta_desc = soup.find("meta", attrs={"name": "description"})
        desc = meta_desc.get("content", "") if meta_desc else f"{brand_name} official website"
    except:
        title_text = brand_name
        desc = f"{brand_name} official website"

    schemas = {
        "organization.jsonld": {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": brand_name,
            "url": base_url,
            "description": desc,
            "sameAs": [
                f"https://twitter.com/{brand_name}",
                f"https://www.linkedin.com/company/{brand_name}",
                f"https://github.com/{brand_name}",
            ]
        },
        "website.jsonld": {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": title_text,
            "url": base_url,
            "description": desc,
            "potentialAction": {
                "@type": "SearchAction",
                "target": {
                    "@type": "EntryPoint",
                    "urlTemplate": f"{base_url}/search?q={{search_term_string}}"
                },
                "query-input": "required name=search_term_string"
            }
        },
        "faq.jsonld": {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": f"What is {brand_name}?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": f"{desc}"
                    }
                },
                {
                    "@type": "Question",
                    "name": f"How does {brand_name} work?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": "Visit our website to learn more about our products and services."
                    }
                },
                {
                    "@type": "Question",
                    "name": f"How can I contact {brand_name}?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": f"Visit {base_url}/contact for more information."
                    }
                }
            ]
        }
    }

    return json.dumps(schemas, indent=2, ensure_ascii=False)


def run_fix(url: str, check_only: bool = False) -> dict:
    """Run the geo fix check and generate missing files."""
    domain_dir = get_domain_dir(url)

    result = {
        "url": url,
        "domain_dir": domain_dir,
        "checked": {},
        "generated": {},
        "errors": [],
    }

    # Check what exists
    print(f"Checking {url}...")

    # Check llms.txt
    llms = check_llms_txt(url)
    result["checked"]["llms_txt"] = llms["exists"]
    print(f"  llms.txt: {'EXISTS' if llms['exists'] else 'MISSING'}")

    # Check robots.txt
    robots = check_robots_txt(url)
    result["checked"]["robots_txt"] = robots["exists"]
    result["checked"]["robots_txt_issues"] = robots["ai_crawlers_blocked"]
    print(f"  robots.txt: {'EXISTS' if robots['exists'] else 'MISSING'}")

    # Check JSON-LD
    jsonld = check_json_ld(url)
    result["checked"]["jsonld"] = jsonld
    print(f"  JSON-LD found: {jsonld['found'] if jsonld['found'] else 'NONE'}")
    print(f"  JSON-LD issues: {jsonld['issues'] if jsonld['issues'] else 'NONE'}")

    # Determine what needs to be generated
    needs_generation = []

    if not llms["exists"]:
        needs_generation.append("llms.txt")

    if not robots["exists"]:
        needs_generation.append("robots.txt")
    elif robots["ai_crawlers_blocked"]:
        needs_generation.append("robots.txt (AI crawler rules)")

    if not jsonld["found"] or "Organization" not in jsonld["found"]:
        needs_generation.append("schema (organization)")

    if not jsonld["found"] or "WebSite" not in jsonld["found"]:
        needs_generation.append("schema (website)")

    if not jsonld["found"] or "FAQPage" not in jsonld["found"]:
        needs_generation.append("schema (faq)")

    if not needs_generation:
        print("\n✓ All GEO files are present!")
        return result

    print(f"\nGenerating missing files: {', '.join(needs_generation)}")

    if check_only:
        print("\n[Check only mode - no files generated]")
        result["would_generate"] = needs_generation
        return result

    # Create directory
    if not os.path.exists(domain_dir):
        os.makedirs(domain_dir)
        print(f"  Created directory: {domain_dir}/")

    # Generate files
    if "llms.txt" in needs_generation:
        llms_content = generate_llms_txt(url)
        llms_path = os.path.join(domain_dir, "llms.txt")
        with open(llms_path, "w") as f:
            f.write(llms_content)
        result["generated"]["llms.txt"] = llms_path
        print(f"  Generated: {llms_path}")

    if "robots.txt" in needs_generation or "robots.txt (AI crawler rules)" in needs_generation:
        robots_content = generate_robots_txt(url)
        robots_path = os.path.join(domain_dir, "robots.txt")
        with open(robots_path, "w") as f:
            f.write(robots_content)
        result["generated"]["robots.txt"] = robots_path
        print(f"  Generated: {robots_path}")

    # Generate schema files
    schema_needs = [s for s in needs_generation if s.startswith("schema")]
    if schema_needs:
        schemas = json.loads(generate_schema_jsonld(url))

        for schema_key, schema_data in schemas.items():
            # Check if this schema type was needed
            schema_type = schema_data.get("@type", "")
            if schema_type == "Organization" and "schema (organization)" not in schema_needs:
                continue
            if schema_type == "WebSite" and "schema (website)" not in schema_needs:
                continue
            if schema_type == "FAQPage" and "schema (faq)" not in schema_needs:
                continue

            schema_path = os.path.join(domain_dir, schema_key)
            with open(schema_path, "w") as f:
                json.dump(schema_data, f, indent=2, ensure_ascii=False)
            result["generated"][schema_key] = schema_path
            print(f"  Generated: {schema_path}")

    # Create README
    parsed = urlparse(url)
    readme_content = f"""# GEO Fix Output — {url}

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Files Generated

{chr(10).join([f"- `{os.path.basename(v)}`" for v in result["generated"].values()])}

## How to Deploy

### llms.txt
Upload `llms.txt` to your web server root (/{domain_dir}/llms.txt → https://{parsed.netloc}/llms.txt)

### robots.txt
Upload `robots.txt` to your web server root to ensure AI crawlers can access your content.

### JSON-LD Schemas
Add these to your homepage HTML <head> section:

```html
<!-- Organization Schema -->
<script type="application/ld+json" src="{domain_dir}/organization.jsonld"></script>

<!-- Website Schema -->
<script type="application/ld+json" src="{domain_dir}/website.jsonld"></script>

<!-- FAQ Schema -->
<script type="application/ld+json" src="{domain_dir}/faq.jsonld"></script>
```

Or copy the JSON-LD content directly into existing <script type="application/ld+json"> tags.

## Notes

- These files are starting points - review and customize before deployment
- llms.txt content is based on discovered pages - add/remove pages as needed
- JSON-LD schemas may need additional properties specific to your business
"""

    readme_path = os.path.join(domain_dir, "README.md")
    with open(readme_path, "w") as f:
        f.write(readme_content)
    result["generated"]["README.md"] = readme_path
    print(f"  Generated: {readme_path}")

    print(f"\n✓ GEO fix complete! Files saved to: {domain_dir}/")

    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python geo_fix.py <url> [--check-only]")
        print("Example: python geo_fix.py https://www.example.com")
        sys.exit(1)

    url = sys.argv[1]
    check_only = "--check-only" in sys.argv

    result = run_fix(url, check_only)

    if result["generated"]:
        print("\n--- Summary ---")
        for fname, fpath in result["generated"].items():
            print(f"  {fname}: {fpath}")