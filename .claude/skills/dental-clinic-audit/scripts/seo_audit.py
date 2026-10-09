#!/usr/bin/env python3
"""Технический SEO- и конверсионный аудит сайта стоматологии.

Только стандартная библиотека Python 3.9+. Запуск:
    python3 seo_audit.py https://clinic.ru [--max-pages 40] [--out report.md]

Собирает: robots.txt, sitemap.xml, редирект на https, по каждой странице —
статус, время ответа, вес, title, description, H1, canonical, noindex, schema.org,
телефоны, формы, alt у картинок. По сайту — покрытие страниц услуг, юридические
страницы, счётчики/коллтрекинг, дубли title. Отчёт — Markdown.
"""
import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, deque
from html.parser import HTMLParser

UA = "Mozilla/5.0 (compatible; DentalAuditBot/1.0)"
TIMEOUT = 20

SERVICES = {
    "Имплантация": r"имплант",
    "All-on-4/6": r"all[\s-]?on|все на (4|6|четыр|шест)",
    "Протезирование": r"протез",
    "Коронки": r"корон",
    "Виниры": r"винир",
    "Брекеты": r"брекет",
    "Элайнеры": r"элайнер|капп",
    "Лечение кариеса": r"кариес",
    "Лечение каналов": r"канал|эндодонт|пульпит",
    "Удаление зубов": r"удален",
    "Гигиена": r"гигиен|чистк",
    "Отбеливание": r"отбелив",
    "Детская стоматология": r"детск",
    "Пародонтология": r"пародонт|десн",
    "КТ/диагностика": r"\bкт\b|томограф|диагност",
    "Лечение во сне": r"во сне|седац|наркоз",
}
LEGAL = {
    "Лицензия": r"лиценз",
    "Политика ПДн": r"персональн|политик[аи] конфиденц|privacy",
    "Цены/прайс": r"цен[аы]|прайс|стоимост",
    "Врачи": r"врач|доктор|специалист",
    "Отзывы": r"отзыв",
    "Контакты": r"контакт",
    "Противопоказания": r"противопоказан",
}
TRACKERS = {
    "Яндекс Метрика": r"mc\.yandex\.ru|ym\(\d+",
    "VK пиксель": r"vk\.com/rtrg|top-fwz1\.mail\.ru|_tmr",
    "Roistat": r"roistat",
    "Calltouch": r"calltouch",
    "CoMagic/UIS": r"comagic|uiscom",
    "Callibri": r"callibri",
    "Google Analytics/GTM": r"googletagmanager|google-analytics|gtag\(",
    "Google Fonts": r"fonts\.googleapis",
    "reCAPTCHA": r"recaptcha",
    "Jivo/чат": r"jivosite|jivo|bitrix24.*crm|livetex|envybox",
    "Квиз (Marquiz и др.)": r"marquiz|quizgo|enquiz",
}
SKIP_EXT = re.compile(r"\.(jpg|jpeg|png|gif|webp|svg|pdf|zip|rar|docx?|xlsx?|mp4|mp3|css|js|ico|woff2?)$", re.I)


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.in_title = False
        self.meta = {}
        self.h1 = []
        self.in_h1 = False
        self.links = []
        self.canonical = ""
        self.images = 0
        self.images_no_alt = 0
        self.forms = 0
        self.tel = set()
        self.ld_json = []
        self.in_ld = False
        self.ld_buf = ""
        self.text = []
        self.skip_text = 0

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "title":
            self.in_title = True
        elif tag == "meta":
            key = (a.get("name") or a.get("property") or "").lower()
            if key:
                self.meta[key] = a.get("content", "")
        elif tag == "h1":
            self.in_h1 = True
            self.h1.append("")
        elif tag == "a":
            href = a.get("href", "")
            if href.startswith("tel:"):
                self.tel.add(re.sub(r"[^\d+]", "", href[4:]))
            elif href:
                self.links.append(href)
        elif tag == "link" and "canonical" in a.get("rel", "").lower():
            self.canonical = a.get("href", "")
        elif tag == "img":
            self.images += 1
            if not a.get("alt", "").strip():
                self.images_no_alt += 1
        elif tag == "form":
            self.forms += 1
        elif tag == "script":
            if "ld+json" in a.get("type", ""):
                self.in_ld = True
                self.ld_buf = ""
            self.skip_text += 1
        elif tag == "style":
            self.skip_text += 1

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        elif tag == "h1":
            self.in_h1 = False
        elif tag == "script":
            if self.in_ld:
                self.ld_json.append(self.ld_buf)
                self.in_ld = False
            self.skip_text = max(0, self.skip_text - 1)
        elif tag == "style":
            self.skip_text = max(0, self.skip_text - 1)

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        if self.in_h1 and self.h1:
            self.h1[-1] += data
        if self.in_ld:
            self.ld_buf += data
        elif not self.skip_text:
            self.text.append(data)


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "ru"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            body = r.read()
            charset = r.headers.get_content_charset() or "utf-8"
            return {"status": r.status, "url": r.geturl(), "body": body.decode(charset, "replace"),
                    "bytes": len(body), "ms": int((time.time() - t0) * 1000),
                    "ctype": r.headers.get("Content-Type", "")}
    except urllib.error.HTTPError as e:
        return {"status": e.code, "url": url, "body": "", "bytes": 0,
                "ms": int((time.time() - t0) * 1000), "ctype": ""}
    except Exception as e:  # noqa: BLE001 — отчёт должен собраться даже при сетевых ошибках
        return {"status": 0, "url": url, "body": "", "bytes": 0, "ms": 0, "ctype": "", "error": str(e)}


def schema_types(blocks):
    types = set()

    def walk(node):
        if isinstance(node, dict):
            t = node.get("@type")
            if isinstance(t, list):
                types.update(map(str, t))
            elif t:
                types.add(str(t))
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    for b in blocks:
        try:
            walk(json.loads(b))
        except ValueError:
            types.add("невалидный JSON-LD")
    return types


def norm(url, base):
    u = urllib.parse.urljoin(base, url.split("#")[0])
    p = urllib.parse.urlparse(u)
    return urllib.parse.urlunparse((p.scheme, p.netloc.lower(), p.path or "/", "", p.query, ""))


def sitemap_urls(root):
    found, queue, seen = [], deque([root + "/sitemap.xml"]), set()
    robots = fetch(root + "/robots.txt")
    if robots["status"] == 200:
        for m in re.findall(r"(?im)^sitemap:\s*(\S+)", robots["body"]):
            queue.appendleft(m)
    while queue and len(seen) < 10:
        sm = queue.popleft()
        if sm in seen:
            continue
        seen.add(sm)
        r = fetch(sm)
        if r["status"] != 200:
            continue
        locs = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", r["body"])
        if "<sitemapindex" in r["body"]:
            queue.extend(locs)
        else:
            found.extend(locs)
    return robots, sorted(seen), found


def audit(start, max_pages):
    start = start if start.startswith("http") else "https://" + start
    p = urllib.parse.urlparse(start)
    root = f"{p.scheme}://{p.netloc}"
    host = p.netloc.lower().removeprefix("www.")
    site = {"root": root}

    http = fetch("http://" + p.netloc + "/")
    site["http_to_https"] = http.get("url", "").startswith("https://")
    site["home"] = fetch(root + "/")
    robots, sitemaps, sm_urls = sitemap_urls(root)
    site["robots"] = robots["status"]
    site["sitemaps"] = sitemaps
    site["sitemap_urls"] = len(sm_urls)
    site["404"] = fetch(root + "/this-page-should-not-exist-404-check").get("status")

    queue = deque([norm(start, start)] + [norm(u, root) for u in sm_urls])
    seen, pages = set(), []
    while queue and len(pages) < max_pages:
        url = queue.popleft()
        if url in seen or SKIP_EXT.search(urllib.parse.urlparse(url).path):
            continue
        seen.add(url)
        r = fetch(url)
        if "html" not in r["ctype"] and r["status"] == 200:
            continue
        pp = PageParser()
        try:
            pp.feed(r["body"])
        except Exception:  # noqa: BLE001 — битая разметка не должна ронять аудит
            pass
        text = re.sub(r"\s+", " ", " ".join(pp.text))
        pages.append({
            "url": url, "status": r["status"], "ms": r["ms"], "kb": r["bytes"] // 1024,
            "title": pp.title.strip(), "desc": pp.meta.get("description", "").strip(),
            "h1": [h.strip() for h in pp.h1 if h.strip()], "canonical": pp.canonical,
            "noindex": "noindex" in pp.meta.get("robots", "").lower(),
            "schema": schema_types(pp.ld_json), "tel": pp.tel, "forms": pp.forms,
            "img": pp.images, "img_no_alt": pp.images_no_alt, "words": len(text.split()),
            "html": r["body"], "text": text.lower(), "viewport": "viewport" in pp.meta,
        })
        for href in pp.links:
            u = norm(href, url)
            if urllib.parse.urlparse(u).netloc.lower().removeprefix("www.") == host and u not in seen:
                queue.append(u)
    return site, pages


def report(site, pages):
    out = []
    w = out.append
    home = site["home"]
    w(f"# SEO-аудит: {site['root']}\n")
    w(f"Проверено страниц: {len(pages)} · Дата: {time.strftime('%Y-%m-%d')}\n")
    if home["status"] != 200:
        w(f"> ⚠️ Главная ответила статусом {home['status']} {home.get('error', '')}. "
          "Возможно, сайт недоступен из этой сети — запустите скрипт локально.\n")

    w("## Сайт целиком\n")
    w("| Проверка | Результат |\n|---|---|")
    w(f"| Редирект http → https | {'✅' if site['http_to_https'] else '❌ нет'} |")
    w(f"| robots.txt | {'✅' if site['robots'] == 200 else '❌ ' + str(site['robots'])} |")
    w(f"| sitemap.xml | {('✅ ' + str(site['sitemap_urls']) + ' URL') if site['sitemap_urls'] else '❌ не найден'} |")
    w(f"| Корректный 404 | {'✅' if site['404'] == 404 else '❌ статус ' + str(site['404'])} |")
    w(f"| Время ответа главной | {home['ms']} мс, {home['bytes'] // 1024} КБ HTML |")
    viewport = pages[0]["viewport"] if pages else False
    w(f"| Мобильный viewport | {'✅' if viewport else '❌'} |\n")

    all_html = " ".join(p["html"] for p in pages).lower()
    all_text = " ".join(p["text"] + " " + p["url"].lower() + " " + p["title"].lower() for p in pages)
    inner = [p for p in pages if urllib.parse.urlparse(p["url"]).path not in ("", "/")]
    urls_titles = " ".join(p["url"].lower() + " " + p["title"].lower() + " " + " ".join(p["h1"]).lower() for p in inner)

    w("## Страницы услуг (внутренние страницы, по URL/title/H1; главная не считается)\n")
    w("| Услуга | Отдельная страница | Упоминание в тексте |\n|---|---|---|")
    for name, rx in SERVICES.items():
        page = bool(re.search(rx, urls_titles))
        txt = bool(re.search(rx, all_text))
        w(f"| {name} | {'✅' if page else '❌'} | {'✅' if txt else '—'} |")
    w("")

    w("## Обязательная информация и доверие\n")
    w("| Блок | Найдено |\n|---|---|")
    for name, rx in LEGAL.items():
        w(f"| {name} | {'✅' if re.search(rx, all_text) else '❌ не найдено'} |")
    tels = set().union(*[p["tel"] for p in pages]) if pages else set()
    w(f"| Кликабельные телефоны | {', '.join(sorted(tels)) or '❌ нет tel:-ссылок'} |")
    w(f"| Формы | {'✅ на ' + str(sum(1 for p in pages if p['forms'])) + ' стр.' if any(p['forms'] for p in pages) else '❌ нет <form>'} |")
    schemas = set().union(*[p["schema"] for p in pages]) if pages else set()
    med = {"Dentist", "MedicalClinic", "MedicalOrganization", "LocalBusiness", "Physician"}
    w(f"| Schema.org | {', '.join(sorted(schemas)) or '❌ нет JSON-LD'} {'' if schemas & med else '(нет Dentist/MedicalClinic)'} |\n")

    w("## Аналитика и сторонние сервисы\n")
    w("| Сервис | Найден |\n|---|---|")
    for name, rx in TRACKERS.items():
        w(f"| {name} | {'✅' if re.search(rx, all_html) else '—'} |")
    w("\n> Google Analytics/Fonts/reCAPTCHA — проверить риски по 152-ФЗ (трансграничная передача ПДн).\n")

    w("## Проблемы мета-тегов\n")
    titles = Counter(p["title"] for p in pages if p["title"])
    issues = []
    for p in pages:
        u = p["url"]
        if p["status"] != 200:
            issues.append(f"| {u} | статус {p['status']} |")
            continue
        if not p["title"]:
            issues.append(f"| {u} | нет title |")
        elif len(p["title"]) > 70 or len(p["title"]) < 20:
            issues.append(f"| {u} | title {len(p['title'])} симв. |")
        if titles.get(p["title"], 0) > 1:
            issues.append(f"| {u} | дубль title |")
        if not p["desc"]:
            issues.append(f"| {u} | нет description |")
        if len(p["h1"]) != 1:
            issues.append(f"| {u} | H1: {len(p['h1'])} шт. |")
        if p["noindex"]:
            issues.append(f"| {u} | noindex |")
        if p["img_no_alt"]:
            issues.append(f"| {u} | {p['img_no_alt']}/{p['img']} картинок без alt |")
        if p["ms"] > 1500:
            issues.append(f"| {u} | медленный ответ {p['ms']} мс |")
        if p["words"] < 250:
            issues.append(f"| {u} | мало текста ({p['words']} слов) |")
    if issues:
        w("| Страница | Проблема |\n|---|---|")
        out.extend(issues[:200])
    else:
        w("Явных проблем не найдено.")
    w("")

    w("## Страницы\n")
    w("| URL | Статус | мс | КБ | Title | H1 |\n|---|---|---|---|---|---|")
    for p in pages:
        t = p["title"].replace("|", "/")[:70]
        h = (p["h1"][0] if p["h1"] else "—").replace("|", "/")[:60]
        w(f"| {p['url']} | {p['status']} | {p['ms']} | {p['kb']} | {t} | {h} |")
    w("\n_Скорость и Core Web Vitals проверьте отдельно в PageSpeed Insights (mobile)._")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("url")
    ap.add_argument("--max-pages", type=int, default=40)
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    site, pages = audit(a.url, a.max_pages)
    md = report(site, pages)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"Отчёт: {a.out}")
    else:
        sys.stdout.write(md + "\n")


if __name__ == "__main__":
    main()
