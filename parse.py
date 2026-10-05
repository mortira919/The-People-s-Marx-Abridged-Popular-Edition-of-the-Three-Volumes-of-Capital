"""Качает книгу с loveread и режет по главам: kapital.txt + kapital.html."""
import html, re, urllib.request
from pathlib import Path

BOOK, PAGES = 81484, 102
HERE = Path(__file__).parent
CACHE = HERE / "pages"


def page(n):
    f = CACHE / f"{n}.html"
    if not f.exists():
        CACHE.mkdir(exist_ok=True)
        req = urllib.request.Request(f"https://loveread.ec/read_book.php?id={BOOK}&p={n}",
                                     headers={"User-Agent": "Mozilla/5.0"})
        f.write_bytes(urllib.request.urlopen(req).read())
    return f.read_text(encoding="utf-8")


TOKEN = re.compile(r'<div class="book-title">(.*?)</div>|<div class=em>|</div>|<p class=(?:MsoNormal|"book-subtitle")>(.*?)</p>', re.S)


def chapters():
    out, cur, quote = [], None, False
    for n in range(1, PAGES + 1):
        h = page(n)
        h = h[h.find('class="number-page-book"'):h.find('class="navigation"')]
        h = h[h.find("</div>") + 6:]  # пропускаем сам номер страницы
        for m in TOKEN.finditer(h):
            if m.group(1) is not None:
                lines = [" ".join(html.unescape(re.sub("<[^>]+>", "", x)).split()) for x in re.split(r"<br\s*/?\s*>", m.group(1))]
                cur = {"title": [x for x in lines if x], "paras": []}
                out.append(cur)
            elif m.group(0) == "<div class=em>":
                quote = True
            elif m.group(0) == "</div>":
                quote = False
            elif cur is not None:
                body = re.sub(r"<(?!/?(i|b|sup|em|strong)\b)[^>]+>", "", m.group(2)).strip()
                if body:
                    cur["paras"].append((quote, body))
    return out


def to_text(s):
    return html.unescape(re.sub("<[^>]+>", "", s))


def main():
    chs = chapters()
    txt = []
    for c in chs:
        txt += ["", "=" * 60, *c["title"], "=" * 60, ""]
        txt += [("    > " if q else "    ") + to_text(p) for q, p in c["paras"]]
    (HERE / "kapital.txt").write_text("\n".join(txt).strip() + "\n", encoding="utf-8")

    toc = "".join(f'<li{"" if re.match(r"Глава|Пред|От ", c["title"][0]) else " class=sub"}><a href="#c{i}">{html.escape(" — ".join(c["title"][:2]))}</a></li>' for i, c in enumerate(chs))
    body = "".join(
        f'<section id="c{i}"><h2>{"<br>".join(html.escape(t) for t in c["title"])}</h2>'
        + "".join(f'<blockquote>{p}</blockquote>' if q else f"<p>{p}</p>" for q, p in c["paras"])
        + "</section>" for i, c in enumerate(chs))
    tpl = (HERE / "template.html").read_text(encoding="utf-8")
    (HERE / "kapital.html").write_text(tpl.replace("{{TOC}}", toc).replace("{{BODY}}", body), encoding="utf-8")
    print(len(chs), "глав")
    for c in chs:
        print(f'  {" / ".join(c["title"][:2])}: {len(c["paras"])} абз.')


if __name__ == "__main__":
    main()
