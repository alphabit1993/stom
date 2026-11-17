# -*- coding: utf-8 -*-
import json, os, re, html, sys
sys.path.insert(0, os.path.dirname(__file__))
from cases import CASES as ARTICLES
from posts import POSTS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://sinkov-stom.ru"
AUTHOR = "Антон Синьков"
TG = "https://t.me/anton_sinkoff"
MAX = "https://max.ru/u/f9LHodD0cOIT1VEznO4nnYmrbI-MIS4GqPTEwJgVr9NFTOhI5VN9d0u2f9A"
VC = "https://vc.ru/id521693"
MONTHS = ["января","февраля","марта","апреля","мая","июня","июля","августа","сентября","октября","ноября","декабря"]
# порядок кейсов как на главной
ORDER = ["yandex-direkt-dlya-stomatologii","target-vkontakte-dlya-stomatologii","obzvon-bazy-patsientov-stomatologii","partnerskaya-programma-dlya-stomatologii","kupon-snizhenie-stoimosti-vizita-v-stomatologiyu"]
ARTICLES.sort(key=lambda a: ORDER.index(a["slug"]))

def rdate(d): y, m, dd = d.split("-"); return f"{int(dd)} {MONTHS[int(m)-1]} {y}"
def esc(s): return html.escape(s, quote=True)
def plain(s): return re.sub("<[^>]+>", "", s)

KNOT = '<svg class="knot" aria-hidden="true" viewBox="0 0 1060 90"><path d="M10 45 C 50 -10, 110 100, 150 40 S 120 0, 210 25 S 260 90, 190 75 S 180 20, 280 45" fill="none" stroke="#1B1B1B" stroke-width="4" stroke-linecap="round"/><path d="M280 45 L 1050 45" stroke="#D9480F" stroke-width="6" stroke-linecap="round"/></svg>'

HEAD = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
<meta name="robots" content="index, follow">
<meta property="og:type" content="{ogtype}">
<meta property="og:locale" content="ru_RU">
<meta property="og:site_name" content="Антон Синьков — маркетинг для медицинских клиник">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">{ogimg}
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/svg+xml" href="/assets/favicon.svg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Unbounded:wght@500;700;800&family=Manrope:wght@400;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/site.css">
{ld}
</head>
<body>
<div class="w">
<header class="top">
<a class="logo" href="/">Антон Синьков</a>
<nav><a href="/cases/">Кейсы</a><a href="/blog/">Блог</a><a class="btn-o" href="{tg}" target="_blank" rel="noopener">Написать</a></nav>
</header>
"""
FOOT = f"""<footer><span>© {AUTHOR}, маркетинг для медицинских клиник</span><span><a href="/">Главная</a> · <a href="/cases/">Кейсы</a> · <a href="/blog/">Блог</a> · <a href="{TG}" target="_blank" rel="noopener">Telegram</a> · <a href="{MAX}" target="_blank" rel="noopener">MAX</a> · <a href="{VC}" target="_blank" rel="noopener">vc.ru</a></span></footer>
</div>
</body>
</html>
"""
def ldjson(*objs):
    return "\n".join(f'<script type="application/ld+json">{json.dumps(o, ensure_ascii=False)}</script>' for o in objs)
PERSON = {"@type": "Person", "name": AUTHOR, "url": SITE + "/", "sameAs": [TG, VC]}

def contact():
    return f"""<div class="contact"><div class="ph">[фото]</div><div style="flex:1 1 360px;min-width:0"><h2>Хотите так же? Напишите «Хочу разбор»</h2><p>{AUTHOR}, маркетинг для медицинских клиник. 20 минут, бесплатно — покажу, где ваша клиника теряет пациентов.</p></div><div class="pills"><a class="pill a" href="{TG}" target="_blank" rel="noopener">Telegram</a><a class="pill d" href="{MAX}" target="_blank" rel="noopener">MAX</a></div></div>"""

def article_page(a, i):
    url = f"{SITE}/cases/{a['slug']}/"
    toc = "".join(f'<li><a href="#{k}">{plain(t)}</a></li>' for k, t in re.findall(r'<h2 id="([^"]+)">(.*?)</h2>', a["body"])) + '<li><a href="#faq">Частые вопросы</a></li>'
    kpis = "".join(f'<div class="kpi"><b>{v}</b><span>{l}</span></div>' for v, l in a["kpis"])
    tags = "".join(f"<span>{t}</span>" for t in a["tags"])
    faq = "".join(f"<details><summary>{q}</summary><p>{x}</p></details>" for q, x in a["faq"])
    big, sub, txt = a["result"]
    nxt = ARTICLES[(i + 1) % len(ARTICLES)]
    imgs = re.findall(r'src="(/assets/img/[^"]+)"', a["body"])
    ld = ldjson(
        {"@context": "https://schema.org", "@type": "BlogPosting", "headline": plain(a["h1"]), "description": a["description"],
         "datePublished": a["date"], "dateModified": "2026-11-17", "inLanguage": "ru", "mainEntityOfPage": url, "url": url,
         "author": PERSON, "publisher": PERSON, **({"image": [SITE + x for x in imgs]} if imgs else {})},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Главная", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Кейсы", "item": SITE + "/cases/"},
            {"@type": "ListItem", "position": 3, "name": plain(a["h1"]), "item": url}]},
        {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": x}} for q, x in a["faq"]]},
    )
    ogimg = f'\n<meta property="og:image" content="{SITE}{imgs[0]}">' if imgs else ""
    out = HEAD.format(title=esc(a["title"]), desc=esc(a["description"]), url=url, ogtype="article", ogimg=ogimg, ld=ld, tg=TG)
    out += f"""<div class="crumb"><a href="/cases/">Кейсы</a> / {a['tag']} · <time datetime="{a['date']}">{rdate(a['date'])}</time></div>
<h1>{a['h1']}</h1>
<p class="lead">{a['lead']}</p>
<div class="tags">{tags}</div>
<div class="kpis">{kpis}</div>
{KNOT}
<div class="grid">
<nav class="toc" aria-label="Содержание"><p>Содержание</p><ol>{toc}</ol></nav>
<div><article>{a['body']}</article>
<section class="faq"><h2 id="faq">Частые вопросы</h2>{faq}</section></div>
</div>
<div class="after"><div><div class="l">Итог</div><b>{big}</b><div style="font-weight:700">{sub}</div></div><div class="t">{txt}</div></div>
{contact()}
<div class="pager"><a href="/cases/">← Все кейсы</a><a href="/cases/{nxt['slug']}/">Следующий: {plain(nxt['h1'])} →</a></div>
"""
    out += FOOT
    d = f"{ROOT}/cases/{a['slug']}"; os.makedirs(d, exist_ok=True)
    open(f"{d}/index.html", "w").write(out)

def list_page():
    url = SITE + "/cases/"
    title = "Кейсы: маркетинг медицинских клиник с цифрами — Антон Синьков"
    desc = "Реальные кейсы стоматологий простым языком: реклама в Яндексе и ВКонтакте, работа с базой пациентов, рекомендации. Что было, что сделали и что получилось."
    cards = "".join(f"""<a class="card{' dark' if i == 2 else ''}" href="/cases/{a['slug']}/"><div class="m"><span>{a['tag']}</span><time datetime="{a['date']}">{rdate(a['date'])}</time></div><div class="was">{a['before']}</div><h2>{a['h1']}</h2><p style="margin:0">{a['card']}</p><div class="go">Читать кейс →</div></a>""" for i, a in enumerate(ARTICLES))
    ld = ldjson({"@context": "https://schema.org", "@type": "CollectionPage", "name": title, "description": desc, "url": url, "inLanguage": "ru", "author": PERSON,
                 "hasPart": [{"@type": "Article", "headline": plain(a["h1"]), "url": f"{SITE}/cases/{a['slug']}/", "datePublished": a["date"]} for a in ARTICLES]})
    out = HEAD.format(title=esc(title), desc=esc(desc), url=url, ogtype="website", ogimg="", ld=ld, tg=TG)
    out += f"""<h1 class="list-h1">Кейсы: что было, что сделали, что получилось</h1>
<p class="lead">Реальные истории стоматологий — простым языком, без маркетинговых терминов.</p>
{KNOT}
<div class="cards">{cards}</div>
{contact()}
"""
    out += FOOT
    os.makedirs(f"{ROOT}/cases", exist_ok=True)
    open(f"{ROOT}/cases/index.html", "w").write(out)

RUBRICS = ["Реклама", "Администраторы и звонки", "Отзывы и карты", "Работа с базой", "Управление клиникой"]
POSTS.sort(key=lambda p: p["date"], reverse=True)

def blog_list():
    url = SITE + "/blog/"
    title = "Блог о маркетинге медицинских клиник — Антон Синьков"
    desc = "Статьи простым языком для руководителей и управляющих медицинских клиник: как привлекать пациентов, не тратя лишнего. Реклама, звонки, отзывы, работа с базой."
    rub = '<span class="on">Все статьи</span>' + "".join(f"<span>{r}</span>" for r in RUBRICS)
    if POSTS:
        f = POSTS[0]
        feat = f"""<a class="empty" style="display:block;text-decoration:none" href="/blog/{f['slug']}/"><div style="color:#F2B88F;font-weight:700;font-size:15px">Главное · {f['minutes']} мин чтения</div><h2 style="margin-top:12px">{f['h1']}</h2><p>{f['lead']}</p><div style="margin-top:20px;color:#F2B88F;font-weight:700">Читать статью →</div></a>"""
        lst = '<h2 class="u" style="font-size:28px;margin:64px 0 0">Все статьи</h2><div class="posts">' + "".join(f'<a href="/blog/{p["slug"]}/"><b>{p["h1"]}</b><span>{p["rubric"]}</span></a>' for p in POSTS) + "</div>"
    else:
        feat = """<div class="empty"><h2>Первые статьи — совсем скоро</h2><p>Пишу о том, как медицинской клинике привлекать пациентов и не тратить лишнего: реклама, работа администраторов, отзывы, база пациентов. Простым языком, с примерами из практики.</p></div>"""
        lst = ""
    cases = "".join(f'<a href="/cases/{a["slug"]}/"><b>{a["kpis"][0][0]}</b><span>{plain(a["h1"])}</span></a>' for a in ARTICLES[:3])
    ld = ldjson({"@context": "https://schema.org", "@type": "Blog", "name": title, "description": desc, "url": url, "inLanguage": "ru", "author": PERSON,
                 "blogPost": [{"@type": "BlogPosting", "headline": p["h1"], "url": f"{SITE}/blog/{p['slug']}/", "datePublished": p["date"]} for p in POSTS]})
    out = HEAD.format(title=esc(title), desc=esc(desc), url=url, ogtype="website", ogimg="", ld=ld, tg=TG)
    out += f"""<h1 class="list-h1">Блог о маркетинге медицинских клиник — простым языком</h1>
<p class="lead">Как привлекать пациентов, не тратя лишнего. Для руководителей и управляющих клиник.</p>
<div class="rubrics">{rub}</div>
{feat}
{lst}
<div class="ask"><div style="flex:1 1 420px;min-width:0"><h2>Есть вопрос о маркетинге клиники?</h2><p>Напишите — отвечу лично, а самые частые вопросы разберу в статьях.</p></div><a class="pill d" href="{TG}" target="_blank" rel="noopener">Задать вопрос в Telegram</a></div>
<h2 class="u" style="font-size:28px;margin:64px 0 0">Кейсы с цифрами</h2>
<div class="side-cases">{cases}</div>
<p style="margin:16px 0 0"><a href="/cases/" style="color:var(--acc);font-weight:700;text-decoration:none">Все кейсы →</a></p>
{contact()}
"""
    out += FOOT
    os.makedirs(f"{ROOT}/blog", exist_ok=True)
    open(f"{ROOT}/blog/index.html", "w").write(out)

def blog_post(p, i):
    url = f"{SITE}/blog/{p['slug']}/"
    toc = "".join(f'<li><a href="#{k}">{plain(t)}</a></li>' for k, t in re.findall(r'<h2 id="([^"]+)">(.*?)</h2>', p["body"])) + '<li><a href="#faq">Частые вопросы</a></li>'
    cta = '<div class="inline-cta"><div style="flex:1 1 320px;min-width:0"><b>Узнали свою клинику?</b><span>Разберу вашу ситуацию — 20 минут, бесплатно.</span></div><a class="pill a" href="' + TG + '" target="_blank" rel="noopener">Хочу разбор</a></div>'
    body = p["body"].replace("<!--CTA-->", cta)
    c = next((a for a in ARTICLES if a["slug"] == p.get("case")), None)
    if c:
        body += f'<a href="/cases/{c["slug"]}/" class="after" style="text-decoration:none;margin-top:32px;padding:28px"><div><div class="l">Как это выглядит на практике</div><b style="font-size:36px">{c["kpis"][0][0]}</b><div style="font-weight:700">{plain(c["h1"])} →</div></div></a>'
    faq = "".join(f"<details><summary>{q}</summary><p>{x}</p></details>" for q, x in p["faq"])
    rel = [q for q in POSTS if q is not p][:3]
    relh = ('<h2 class="u" style="font-size:26px;margin:64px 0 0">Читайте также</h2><div class="side-cases">' + "".join(f'<a href="/blog/{q["slug"]}/"><span style="color:var(--ink);font-weight:800;font-size:17px">{q["h1"]}</span></a>' for q in rel) + "</div>") if rel else ""
    ld = ldjson(
        {"@context": "https://schema.org", "@type": "BlogPosting", "headline": p["h1"], "description": p["description"], "datePublished": p["date"], "dateModified": p["date"], "inLanguage": "ru", "mainEntityOfPage": url, "url": url, "author": PERSON, "publisher": PERSON},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Главная", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Блог", "item": SITE + "/blog/"},
            {"@type": "ListItem", "position": 3, "name": p["h1"], "item": url}]},
        {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": x}} for q, x in p["faq"]]})
    out = HEAD.format(title=esc(p["title"]), desc=esc(p["description"]), url=url, ogtype="article", ogimg="", ld=ld, tg=TG)
    out += f"""<div class="crumb"><a href="/blog/">Блог</a> / {p['rubric']} · {p['minutes']} мин чтения · <time datetime="{p['date']}">{rdate(p['date'])}</time></div>
<h1>{p['h1']}</h1>
<p class="lead">{p['lead']}</p>
{KNOT}
<div class="grid post">
<div><article><div class="short"><b>Коротко</b><div style="color:var(--soft)">{p['short']}</div></div>{body}</article>
<section class="faq"><h2 id="faq">Частые вопросы</h2>{faq}</section></div>
<aside class="side"><nav class="toc" aria-label="Содержание"><p>Содержание</p><ul style="list-style:none;padding:0">{toc}</ul></nav><div class="box"><b>Разберу вашу рекламу бесплатно</b><span>20 минут, без обязательств</span><a href="{TG}" target="_blank" rel="noopener">Написать в Telegram</a></div></aside>
</div>
{contact().replace('Хотите так же? Напишите «Хочу разбор»', 'Хотите, чтобы этим занялся я?')}
{relh}
"""
    out += FOOT
    d = f"{ROOT}/blog/{p['slug']}"; os.makedirs(d, exist_ok=True)
    open(f"{d}/index.html", "w").write(out)

def redirects():
    for a in ARTICLES:
        d = f"{ROOT}/blog/{a['slug']}"; os.makedirs(d, exist_ok=True)
        to = f"/cases/{a['slug']}/"
        open(f"{d}/index.html", "w").write(f'<!DOCTYPE html><html lang="ru"><head><meta charset="UTF-8"><title>Страница переехала</title><link rel="canonical" href="{SITE}{to}"><meta name="robots" content="noindex"><meta http-equiv="refresh" content="0; url={to}"><script>location.replace("{to}")</script></head><body><a href="{to}">Перейти к кейсу</a></body></html>')

def sitemap():
    latest = "2026-11-17"
    urls = [(SITE + "/", latest, "1.0"), (SITE + "/analytics.html", latest, "0.6"), (SITE + "/cases/", latest, "0.8"), (SITE + "/blog/", latest, "0.8")]
    urls += [(f"{SITE}/cases/{a['slug']}/", latest, "0.7") for a in ARTICLES]
    urls += [(f"{SITE}/blog/{p['slug']}/", p["date"], "0.7") for p in POSTS]
    x = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    x += "".join(f"  <url><loc>{u}</loc><lastmod>{d}</lastmod><priority>{p}</priority></url>\n" for u, d, p in urls)
    open(f"{ROOT}/sitemap.xml", "w").write(x + "</urlset>\n")

for i, a in enumerate(ARTICLES): article_page(a, i)
list_page(); redirects(); blog_list()
for i, p in enumerate(POSTS): blog_post(p, i)
sitemap()
print("ok", len(ARTICLES))
