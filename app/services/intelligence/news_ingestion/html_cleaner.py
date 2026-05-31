import re

TAG_RE = re.compile(r"<[^>]+>")
SCRIPT_RE = re.compile(r"<script.*?>.*?</script>", re.I | re.S)
STYLE_RE = re.compile(r"<style.*?>.*?</style>", re.I | re.S)


def clean_html(html: str) -> str:
    without = SCRIPT_RE.sub("", html)
    without = STYLE_RE.sub("", without)
    text = TAG_RE.sub(" ", without)
    return re.sub(r"\s+", " ", text).strip()
