"""Convert the Fundamento HTML files into Markdown and JSON/CSV.

Usage: python3 -I build.py <source_dir> <output_dir>
Only the public-domain text is kept; markup, links and site extras are dropped.
"""
import csv
import html
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

SRC = Path(sys.argv[1])
OUT = Path(sys.argv[2])
LANGS = ["fr", "en", "de", "ru", "pl"]


# ---------- dictionary ----------
class VortaroParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.entries = []
        self.stack = []          # open entries (main / sub)
        self.depth_strong = 0
        self.span_depth = 0
        self.buf = None          # where text goes
        self.letter = None
        self.in_h3 = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "h3":
            self.in_h3 = True
        if tag == "li" and a.get("class") in ("vortarero", "subvortarero"):
            e = {"radiko": "", "litero": self.letter, "tradukoj": [], "derivajhoj": []}
            if a["class"] == "subvortarero" and self.stack:
                self.stack[-1]["derivajhoj"].append(e)
            else:
                self.entries.append(e)
            self.stack.append(e)
            self.state = "head"
            return
        if not self.stack:
            return
        if tag == "strong" and self.state == "head":
            self.buf = "head"
        elif tag == "span" and self.span_depth == 0 and self.state in ("head", "body"):
            self.state = "body"
            self.stack[-1]["tradukoj"].append("")
            self.span_depth = 1
            return
        if tag == "span" and self.span_depth:
            self.span_depth += 1
        if tag == "ul":
            self.state = "sub"

    def handle_endtag(self, tag):
        if tag == "h3":
            self.in_h3 = False
        if not self.stack:
            return
        if tag == "strong" and self.buf == "head":
            self.buf = None
            self.state = "afterhead"
        elif tag == "span" and self.span_depth:
            self.span_depth -= 1
        elif tag == "li":
            self.stack.pop()
            self.state = "sub" if self.stack else None

    def handle_data(self, data):
        if self.in_h3 and not self.stack:
            self.letter = data.strip()
            return
        if not self.stack:
            return
        e = self.stack[-1]
        if self.buf == "head":
            e["radiko"] += data
        elif self.span_depth:
            e["tradukoj"][-1] += data
        if getattr(self, "state", None) == "afterhead":
            self.state = "head"


def clean(s):
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def shape(e):
    t = [clean(x) for x in e["tradukoj"]]
    while len(t) > 5 and t[0] == "":
        t = t[1:]
    out = {"radiko": clean(e["radiko"]), "litero": e["litero"]}
    if len(t) == 5:
        out.update(dict(zip(LANGS, t)))
    else:
        out["tradukoj"] = t
    if e["derivajhoj"]:
        out["derivajhoj"] = [shape(d) for d in e["derivajhoj"]]
    return out


vp = VortaroParser()
vp.feed((SRC / "universala_vortaro.html").read_text(encoding="utf-8"))
vortaro = [shape(e) for e in vp.entries]

data = OUT / "data"
data.mkdir(parents=True, exist_ok=True)
(data / "universala-vortaro.json").write_text(
    json.dumps(vortaro, ensure_ascii=False, indent=1), encoding="utf-8")

rows = []
for e in vortaro:
    rows.append(e)
    for d in e.get("derivajhoj", []):
        rows.append(d)
with open(data / "universala-vortaro.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["radiko", "radiko_sen_apostrofoj", *LANGS])
    for r in rows:
        w.writerow([r["radiko"], r["radiko"].replace("'", ""),
                    *[r.get(l, "") for l in LANGS]])

irregular = [e["radiko"] for e in rows if "tradukoj" in e]


# ---------- generic HTML -> Markdown ----------
class MdParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.out = []
        self.cur = ""
        self.list_depth = 0
        self.skip = 0
        self.in_body = False

    def flush(self, prefix=""):
        t = re.sub(r"[ \t]*\n[ \t]*", " ", self.cur)
        t = re.sub(r" {2,}", " ", t).strip()
        if t:
            self.out.append(prefix + t)
        self.cur = ""

    def handle_starttag(self, tag, attrs):
        if tag == "body":
            self.in_body = True
        if tag in ("script", "style", "head"):
            self.skip += 1
        if tag in ("h1", "h2", "h3", "h4", "p", "li", "tr", "div", "hr", "table"):
            self.flush_pending()
        if tag == "br":
            self.cur += " "
        if tag in ("strong", "b"):
            self.cur += "**"
        if tag in ("em", "i"):
            self.cur += "*"
        if tag == "td":
            self.cur += " | "
        if tag in ("ul", "ol"):
            self.list_depth += 1
        self.pending = tag

    def flush_pending(self):
        p = getattr(self, "kind", None)
        prefix = {"h1": "# ", "h2": "## ", "h3": "### ", "h4": "#### ",
                  "li": "  " * max(self.list_depth - 1, 0) + "- "}.get(p, "")
        self.flush(prefix)

    def handle_endtag(self, tag):
        if tag in ("script", "style", "head"):
            self.skip -= 1
        if tag in ("strong", "b"):
            self.cur = self.cur.rstrip() + "** "
        if tag in ("em", "i"):
            self.cur = self.cur.rstrip() + "* "
        if tag == "tr":
            self.cur = self.cur.rstrip() + " |"
        if tag in ("h1", "h2", "h3", "h4", "p", "li", "tr", "div", "table"):
            self.kind = tag
            self.flush_pending()
            self.kind = None
        if tag in ("ul", "ol"):
            self.list_depth -= 1

    def handle_starttag_kind(self, tag):
        pass

    def handle_data(self, data):
        if self.skip or not self.in_body:
            return
        self.cur += data


def to_markdown(path):
    p = MdParser()
    p.kind = None
    orig_start = p.handle_starttag

    def start(tag, attrs):
        if tag in ("h1", "h2", "h3", "h4", "li", "p"):
            p.flush_pending()
            p.kind = tag
        orig_start(tag, attrs)
    p.handle_starttag = start
    p.feed(path.read_text(encoding="utf-8").split('<div id="menuoj"', 1)[0])
    p.flush_pending()
    text = "\n\n".join(html.unescape(x) for x in p.out)
    text = re.sub(r"\*\*\s*\*\*", "", text)
    text = re.sub(r"\*\*\s+([.,;:!?)])", r"**\1", text)
    text = re.sub(r"(?<!\*)\*\s+([.,;:!?)])", r"*\1", text)
    return text.strip() + "\n"


teksto = OUT / "teksto"
teksto.mkdir(parents=True, exist_ok=True)
names = {
    "antauparolo.html": "1-antauparolo.md",
    "gramatiko_franca.html": "2-gramatiko-fr.md",
    "gramatiko_angla.html": "2-gramatiko-en.md",
    "gramatiko_germana.html": "2-gramatiko-de.md",
    "gramatiko_rusa.html": "2-gramatiko-ru.md",
    "gramatiko_pola.html": "2-gramatiko-pl.md",
    "ekzercaro.html": "3-ekzercaro.md",
}
for src, dst in names.items():
    (teksto / dst).write_text(to_markdown(SRC / src), encoding="utf-8")


# ---------- the 16 rules ----------
def rules_from(path):
    """Split on the numbered list markers. Order defines the rule number;
    the printed number is kept separately (the 1905 English edition prints
    '15.' where rule 13 stands)."""
    raw = path.read_text(encoding="utf-8")
    raw = raw.split('<div id="enhavo">', 1)[-1]
    raw = raw.split('<div id="menuoj"', 1)[0]
    raw = re.sub(r"<h2.*?</h2>", " ", raw, flags=re.S)
    raw = re.sub(r'<span class="numero-en-listo">\s*(\d+)\.\s*</span>', r" §§\1§§ ", raw)
    raw = re.sub(r"<ul[^>]*>\s*</ul>", " ", raw)
    plain = re.sub(r"<[^>]+>", " ", raw)
    plain = re.sub(r"\s+", " ", html.unescape(plain))
    parts = re.split(r"§§(\d+)§§", plain)
    items = []
    for i in range(1, len(parts), 2):
        t = parts[i + 1].strip()
        t = re.sub(r"\s+([,.;:!?)\]”»])", r"\1", t)
        t = re.sub(r"([(\[„«])\s+", r"\1", t)
        items.append((int(parts[i]), t))
    return items


rules = {n: {"n": n} for n in range(1, 17)}
problems = {}
for lang, f in zip(LANGS, ["gramatiko_franca", "gramatiko_angla", "gramatiko_germana",
                           "gramatiko_rusa", "gramatiko_pola"]):
    items = rules_from(SRC / f"{f}.html")
    if len(items) != 16:
        problems[lang] = len(items)
    for idx, (printed, text) in enumerate(items[:16], start=1):
        rules[idx][lang] = text
        if printed != idx:
            rules[idx].setdefault("presita_numero", {})[lang] = printed
            problems.setdefault("misnumbered", []).append(f"{lang}: {idx} printed as {printed}")
(data / "reguloj.json").write_text(
    json.dumps(list(rules.values()), ensure_ascii=False, indent=1), encoding="utf-8")

print(json.dumps({
    "radikoj": len(vortaro),
    "kun_derivajhoj": len(rows),
    "neregulaj": irregular[:20],
    "neregulaj_nombro": len(irregular),
    "regulo_problemoj": problems,
}, ensure_ascii=False, indent=1))
