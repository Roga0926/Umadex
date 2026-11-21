#!/usr/bin/env python3
"""Genera páginas estáticas para buscadores a partir de los datos de index.html.

Crea:
  uma/<slug>/index.html      una página por personaje (resumen + enlace a la ficha completa)
  uma/index.html             índice de todos los personajes
  carrera/<id>/index.html    una página por carrera G1 (ganadores desde 1980 + enlace)
  carrera/index.html         índice de carreras
  sitemap.xml y robots.txt

Uso (desde la carpeta del repositorio):  python3 tools/gen_paginas.py
Se vuelve a ejecutar cada vez que cambia index.html; borra y regenera uma/ y carrera/.
"""
import html, json, os, re, shutil, sys, unicodedata, datetime

SITIO = 'https://umadexfan.com'
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def cargar():
    txt = open(os.path.join(RAIZ, 'index.html'), encoding='utf8').read()
    m = re.search(r'<script type="application/json" id="jra-data">(.*?)</script>', txt, re.S)
    if not m:
        sys.exit('No se encontraron los datos (jra-data) en index.html')
    return json.loads(m.group(1))

def e(s):
    return html.escape(str(s if s is not None else ''), quote=True)

def slug(s):
    s = unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode()
    s = re.sub(r'[^a-zA-Z0-9]+', '-', s).strip('-').lower()
    return s or 'x'

def ord_es(n):
    return f'{n}.º'

SEXO = {'macho': 'Macho', 'hembra': 'Hembra', 'castrado': 'Castrado'}
PAIS = {'JPN': 'Japón', 'USA': 'Estados Unidos', 'GB': 'Reino Unido', 'GBR': 'Reino Unido', 'IRE': 'Irlanda',
        'FR': 'Francia', 'FRA': 'Francia', 'ITY': 'Italia', 'ITA': 'Italia', 'NZ': 'Nueva Zelanda', 'NZL': 'Nueva Zelanda',
        'AUS': 'Australia', 'CAN': 'Canadá', 'KSA': 'Arabia Saudita', 'UAE': 'Emiratos Árabes Unidos', 'HK': 'Hong Kong', 'HKG': 'Hong Kong'}

CSS = """
:root{--bg:#0d1511;--surface:#14201a;--sunk:#1a2921;--line:#2a3b31;--ink:#e6eee8;--muted:#9db0a3;--turf:#2f9a5a;--turf-tx:#4fd47e;--turf-ink:#06110a;--gold:#f2c230;--g1:#6f98ff;--g2:#ff6b6b;--g3:#4fc276;color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 "Zen Kaku Gothic New","Hiragino Sans","Noto Sans JP",system-ui,sans-serif}
a{color:var(--turf-tx)}
.top{background:var(--turf);color:var(--turf-ink)}
.top .w{display:flex;align-items:center;gap:1rem;padding:.55rem 16px;max-width:60rem;margin:0 auto}
.top a{color:inherit;text-decoration:none;font:700 1.5rem "Barlow Condensed","Arial Narrow",sans-serif;letter-spacing:.04em}
.top nav{margin-left:auto;display:flex;gap:.9rem;font-weight:700}
.top nav a{white-space:nowrap;font:700 1rem "Barlow Condensed","Arial Narrow",sans-serif}
.rail{height:6px;background:repeating-linear-gradient(90deg,var(--surface) 0 18px,var(--turf) 18px 36px)}
main{max-width:60rem;margin:0 auto;padding:1.25rem 16px 3rem;display:grid;gap:1.1rem}
h1,h2{font-family:"Barlow Condensed","Arial Narrow",sans-serif;line-height:1.1;margin:0}
h1{font-size:clamp(2rem,6vw,3rem)} h2{font-size:1.45rem}
.miga{font-size:.85rem;color:var(--muted)} .miga a{color:var(--muted)}
.hero{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:1rem 1.5rem;align-items:start}
.hero img{width:10rem;aspect-ratio:1;object-fit:cover;border-radius:8px;border:1px solid var(--line);background:var(--sunk)}
.sub{color:var(--muted);margin:.3rem 0 0}
.panel{background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:1rem;display:grid;gap:.6rem}
dl{display:grid;grid-template-columns:max-content 1fr;gap:.3rem 1rem;margin:0} dt{color:var(--muted)} dd{margin:0}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:.5rem;text-align:center}
.stats div{background:var(--sunk);border-radius:6px;padding:.5rem} .stats b{display:block;font:700 1.8rem "Barlow Condensed",sans-serif}
.stats span{font-size:.72rem;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}
ul.ls{margin:0;padding-left:1.2rem} table{border-collapse:collapse;width:100%;font-size:.9rem}
th{text-align:left;font-size:.72rem;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);border-bottom:2px solid var(--ink);padding:.35rem .4rem}
td:first-child{white-space:nowrap}
td{border-bottom:1px solid var(--line);padding:.35rem .4rem;vertical-align:top} tr.pj td{background:color-mix(in srgb,var(--gold) 14%,transparent)}
.gr{display:inline-block;font:700 .8rem "Barlow Condensed",sans-serif;padding:.15rem .4rem;border-radius:3px;color:#0d1511;background:#8d9a92}
.gr.G1{background:var(--g1)}.gr.G2{background:var(--g2)}.gr.G3{background:var(--g3)}
.cta{justify-self:start;display:inline-block;background:var(--turf);color:var(--turf-ink);font-weight:700;text-decoration:none;padding:.65rem 1.2rem;border-radius:999px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(12rem,1fr));gap:.5rem}
.grid a{display:flex;gap:.6rem;align-items:center;background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:.45rem .6rem;text-decoration:none;color:var(--ink)}
.grid img{width:2.6rem;height:2.6rem;border-radius:6px;object-fit:cover;background:var(--sunk)}
.scroll{overflow-x:auto}
footer{max-width:60rem;margin:0 auto;padding:1rem 16px 2rem;border-top:1px solid var(--line);font-size:.8rem;color:var(--muted)}
@media(max-width:560px){.top .w{gap:.6rem}.top a{font-size:1.25rem}.top nav a{font-size:.9rem}.hero{grid-template-columns:1fr}.hero img{width:8rem;order:-1}.stats{grid-template-columns:repeat(2,1fr)}.top nav{gap:.6rem}}
"""

def pagina(titulo, desc, ruta, cuerpo, imagen=None, migas=()):
    url = SITIO + ruta
    img = SITIO + '/' + imagen if imagen else SITIO + '/og.png'
    mig = ' › '.join([f'<a href="/">Umadex</a>'] + [f'<a href="{e(h)}">{e(t)}</a>' if h else e(t) for t, h in migas])
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(titulo)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{e(url)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Umadex">
<meta property="og:title" content="{e(titulo)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{e(url)}">
<meta property="og:image" content="{e(img)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#2f9a5a">
<link rel="icon" href="/icons/icon-192.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700&family=Zen+Kaku+Gothic+New:wght@400;700&display=swap">
<style>{CSS}</style>
</head>
<body>
<header class="top"><div class="w"><a href="/">UMADEX</a><nav><a href="/uma/">Personajes</a><a href="/carrera/">Carreras G1</a><a href="/#juegos">Juegos</a></nav></div><div class="rail"></div></header>
<main>
<div class="miga">{mig}</div>
{cuerpo}
</main>
<footer>Umadex es un sitio de fans sin fines de lucro, no oficial y sin afiliación ni respaldo de Cygames. Uma Musume: Pretty Derby © Cygames, Inc. Datos de Wikipedia, JBIS, netkeiba y la JRA.</footer>
</body>
</html>
"""

def fusionar(d):
    """Aplica los ajustes publicados (D.publico.ajustes_personajes) y los personajes extra, como hace la página."""
    pub = d.get('publico') or {}
    aj = pub.get('ajustes_personajes') or {}
    out = []
    for p in d['personajes']:
        a = aj.get(str(p['id']))
        out.append({**p, **{k: v for k, v in (a or {}).items() if k not in ('actualizado',)}} if a else p)
    for x in (pub.get('personajes_extra') or {}).values() if isinstance(pub.get('personajes_extra'), dict) else (pub.get('personajes_extra') or []):
        if isinstance(x, dict) and x.get('id') is not None and not any(str(q['id']) == str(x['id']) for q in out):
            out.append(x)
    return out

def imagen_de(d, pid):
    im = ((d.get('publico') or {}).get('imagenes') or {}).get(str(pid))
    src = im.get('src') if isinstance(im, dict) else None
    return src if src and os.path.exists(os.path.join(RAIZ, src)) else None

def g1_num(p):
    return ((p.get('resumen_grados') or {}).get('G1') or {}).get('ganadas') or 0

def gen_uma(d, p, slugs_uma, carreras_por_nombre):
    pid, nombre, real = p['id'], p['personaje'], p.get('caballo_real') or p['personaje']
    jp = p.get('nombre_japones') or ''
    r = p.get('record') or {}
    g1 = g1_num(p)
    ped = p.get('pedigri') or {}
    img = imagen_de(d, pid)
    anio = p.get('anio_nacimiento')
    pais = PAIS.get(p.get('pais_nacimiento'), p.get('pais_nacimiento') or '')
    titulo = f'{nombre}' + (f' ({jp})' if jp else '') + ': historial, pedigrí y G1 | Umadex'
    desc = (f'{nombre} es {"la yegua" if p.get("sexo") == "hembra" else "el caballo"} real {real}' if nombre != real else f'{nombre}') + \
        (f', {"nacida" if p.get("sexo") == "hembra" else "nacido"} en {anio}' if anio else '') + (f' en {pais}' if pais else '') + '. ' + \
        (f'Récord: {r.get("carreras")} carreras, {r.get("victorias")} victorias' if r.get('carreras') else '') + \
        (f', {g1} G1 ganadas' if g1 else '') + \
        (f'. {"Hija" if p.get("sexo") == "hembra" else "Hijo"} de {ped.get("padre")} y {ped.get("madre")}' if ped.get('padre') and ped.get('madre') else '') + \
        '. Historial completo, pedigrí y carreras en Umadex.'
    if p.get('historia'):
        desc = (p['historia'][0] if len(p['historia'][0]) <= 200 else p['historia'][0][:197].rsplit(' ', 1)[0] + '…') + \
            (f' Récord: {r.get("carreras")} carreras, {r.get("victorias")} victorias.' if r.get('carreras') else '')
    hechos = []
    if nombre != real: hechos.append(('Caballo real', real))
    if anio: hechos.append(('Nacimiento', f'{anio}' + (f' · {pais}' if pais else '')))
    if p.get('sexo'): hechos.append(('Sexo', SEXO.get(p['sexo'], p['sexo'])))
    if p.get('pelaje'): hechos.append(('Pelaje', str(p['pelaje']).capitalize()))
    if p.get('entrenador'): hechos.append(('Entrenador', p['entrenador']))
    if p.get('ganancias'): hechos.append(('Ganancias', p['ganancias']))
    def enlace_pj(n):
        s = slugs_uma.get(str(n).strip().lower())
        return f'<a href="/uma/{s}/">{e(n)}</a>' if s else e(n)
    pedi = [('Padre', ped.get('padre')), ('Madre', ped.get('madre')), ('Abuelo materno', ped.get('abuelo_materno') or ped.get('m_p'))]
    cg = p.get('carreras_grupo') or []
    filas = ''.join(f'<tr><td>{e(c.get("fecha",""))}</td><td>{e(c.get("carrera",""))}</td><td><span class="gr {e(c.get("grado",""))}">{e(c.get("grado",""))}</span></td><td>{e(ord_es(c["puesto"]) if isinstance(c.get("puesto"), int) else c.get("puesto",""))}</td></tr>' for c in cg)
    g1l = p.get('g1_ganadas') or []
    vids = [v for v in (p.get('videos') or []) if re.match(r'^https://(www\.)?youtube\.com/watch\?v=[\w-]+$', v.get('url') or '')]
    cuerpo = f"""
<section class="hero">
  <div><h1>{e(nombre)}</h1>
  <p class="sub">{e(jp)}{' · ' if jp else ''}{'Caballo real: ' + e(real) if nombre != real else 'Umamusume: Pretty Derby'}</p>
  <p style="margin:.9rem 0 0"><a class="cta" href="/#p-{e(pid)}">Abrir su ficha completa →</a></p></div>
  {f'<img src="/{e(img)}" alt="{e(nombre)}" width="160" height="160">' if img else ''}
</section>
{f'<section class="panel"><h2>Su historia</h2>' + ''.join(f'<p style="margin:0">{e(x)}</p>' for x in p['historia']) + '</section>' if p.get('historia') else ''}
{f'<section class="panel"><h2>Mira la carrera</h2><ul class="ls">' + ''.join(f'<li><a href="{e(v["url"])}" target="_blank" rel="noopener">{e(v["carrera"])} {e(v["anio"])}</a></li>' for v in vids) + '</ul><p class="sub" style="margin:0">Videos del canal oficial de la JRA en YouTube.</p></section>' if vids else ''}
<section class="panel"><h2>Récord</h2>
  <div class="stats"><div><b>{e(r.get('carreras','—'))}</b><span>Carreras</span></div><div><b>{e(r.get('victorias','—'))}</b><span>Victorias</span></div><div><b>{e(r.get('segundos','—'))}</b><span>2.º lugar</span></div><div><b>{e(r.get('terceros','—'))}</b><span>3.º lugar</span></div></div>
  <dl>{''.join(f'<dt>{e(k)}</dt><dd>{e(v)}</dd>' for k, v in hechos)}</dl>
</section>
{f'<section class="panel"><h2>G1 ganadas ({len(g1l)})</h2><ul class="ls">' + ''.join(f'<li>{e(x)}</li>' for x in g1l) + '</ul></section>' if g1l else ''}
<section class="panel"><h2>Pedigrí</h2><dl>{''.join(f'<dt>{e(k)}</dt><dd>{enlace_pj(v)}</dd>' for k, v in pedi if v)}</dl></section>
{f'<section class="panel"><h2>Carreras de grupo</h2><div class="scroll"><table><thead><tr><th>Fecha</th><th>Carrera</th><th>Grado</th><th>Puesto</th></tr></thead><tbody>{filas}</tbody></table></div></section>' if cg else ''}
<a class="cta" href="/#p-{e(pid)}">Ver la ficha completa en Umadex →</a>
<p class="sub">En la ficha completa: historial carrera por carrera, pedigrí de tres generaciones, comparador, juegos y versión en inglés.</p>
"""
    return pagina(titulo, desc, f'/uma/{slugs_uma[nombre.lower()]}/', cuerpo, img, migas=[('Personajes', '/uma/'), (nombre, None)])

def gen_carrera(d, c, slugs_uma, nombres_pj):
    cid, nombre = c['id'], c['nombre']
    jp = c.get('nombre_japones') or ''
    secciones = [c] + (c.get('carreras') or [])
    def pj_link(ganador):
        base = re.sub(r'\s*\([A-Z]{2,3}\)$', '', str(ganador)).strip()
        s = nombres_pj.get(base.lower())
        return f'<a href="/uma/{s}/">{e(base)}</a>' if s else e(ganador)
    bloques = []
    for sc in secciones:
        gpa = sc.get('ganadores_por_anio') or []
        if not gpa: continue
        anios_pj = {(x.get('anio')) for x in (sc.get('personajes_ganadores') or [])}
        filas = ''.join(f'<tr{" class=\"pj\"" if g.get("anio") in anios_pj else ""}><td>{e(g.get("anio",""))}</td><td>{pj_link(g.get("ganador") or "—")}</td></tr>' for g in reversed(gpa))
        titulo_sc = '' if sc is c else f'<h2>{e(sc.get("nombre",""))}</h2>'
        bloques.append(f'<section class="panel">{titulo_sc}<h2>Ganadores por año</h2><div class="scroll"><table><thead><tr><th>Año</th><th>Ganador</th></tr></thead><tbody>{filas}</tbody></table></div></section>')
    rec = c.get('record') or {}
    ed = c.get('edicion_resumida') or {}
    hechos = [(k, v) for k, v in [('Grado', c.get('grado')), ('Hipódromo', c.get('hipodromo')),
              ('Superficie', str(c.get('superficie') or '').capitalize()), ('Distancia', f"{c['distancia_m']} m" if c.get('distancia_m') else ''),
              ('Condiciones', c.get('condiciones')), ('Récord', f"{rec.get('tiempo')} · {rec.get('caballo')} ({rec.get('anio')})" if rec.get('tiempo') else ''),
              ('Última edición', f"{ed.get('anio')}: {ed.get('ganador')}" if ed.get('ganador') else '')] if v]
    pjs_d = {}
    for x in sorted(c.get('personajes_ganadores') or [], key=lambda x: x.get('anio') or 0):
        a = pjs_d.setdefault(x['personaje'], [])
        if x.get('anio') not in a: a.append(x.get('anio'))
    pjs = [(n, ', '.join(str(y) for y in a)) for n, a in pjs_d.items()]
    desc = f'{nombre}' + (f' ({jp})' if jp else '') + f': carrera {c.get("grado","G1")}' + (f' en {c["hipodromo"]}' if c.get('hipodromo') else '') + \
        (f', {c["distancia_m"]} m' if c.get('distancia_m') else '') + '. Ganadores desde 1980, récord y umas que la ganaron.'
    cuerpo = f"""
<section><h1>{e(nombre)}</h1><p class="sub">{e(jp)}</p><p style="margin:.9rem 0 0"><a class="cta" href="/#g1-{e(cid)}">Abrir la carrera en Umadex →</a></p></section>
<section class="panel"><dl>{''.join(f'<dt>{e(k)}</dt><dd>{e(v)}</dd>' for k, v in hechos)}</dl>{f'<p class="sub">{e(c["historia"])}</p>' if c.get('historia') else ''}</section>
{f'<section class="panel"><h2>Umas que la ganaron</h2><ul class="ls">' + ''.join(f'<li>{pj_link(n)} ({e(a)})</li>' for n, a in pjs) + '</ul></section>' if pjs else ''}
{''.join(bloques)}
<a class="cta" href="/#g1-{e(cid)}">Ver la carrera en Umadex →</a>
"""
    return pagina(f'{nombre}' + (f' ({jp})' if jp else '') + ': ganadores y récord | Umadex', desc, f'/carrera/{cid}/', cuerpo, migas=[('Carreras G1', '/carrera/'), (nombre, None)])

def main():
    d = cargar()
    pjs = fusionar(d)
    usados, slugs_uma = set(), {}
    for p in pjs:
        s = slug(p['personaje'])
        while s in usados: s += f'-{p["id"]}'
        usados.add(s); slugs_uma[p['personaje'].lower()] = s
    nombres_pj = dict(slugs_uma)
    for p in pjs:  # también por nombre del caballo real (para enlazar ganadores y pedigrí)
        nombres_pj.setdefault(str(p.get('caballo_real') or '').lower(), slugs_uma[p['personaje'].lower()])
    for carpeta in ('uma', 'carrera'):
        shutil.rmtree(os.path.join(RAIZ, carpeta), ignore_errors=True)
    urls = [SITIO + '/']
    def escribir(ruta, contenido):
        f = os.path.join(RAIZ, ruta.strip('/'), 'index.html')
        os.makedirs(os.path.dirname(f), exist_ok=True)
        open(f, 'w', encoding='utf8').write(contenido)
        urls.append(SITIO + ruta)
    orden = sorted(pjs, key=lambda p: p['personaje'].lower())
    for p in orden:
        escribir(f'/uma/{slugs_uma[p["personaje"].lower()]}/', gen_uma(d, p, nombres_pj, None))
    items = ''.join(f'<a href="/uma/{slugs_uma[p["personaje"].lower()]}/">' + (f'<img src="/{e(imagen_de(d, p["id"]))}" alt="" loading="lazy">' if imagen_de(d, p['id']) else '') + f'<span>{e(p["personaje"])}</span></a>' for p in orden)
    escribir('/uma/', pagina('Personajes de Umamusume y sus caballos reales | Umadex',
                             f'Los {len(orden)} personajes de Umamusume: Pretty Derby y los caballos reales detrás de cada uno: historial, pedigrí, G1 ganadas y ganancias.',
                             '/uma/', f'<h1>Personajes</h1><p class="sub">{len(orden)} umas y sus caballos reales.</p><div class="grid">{items}</div>', migas=[('Personajes', None)]))
    carreras = d['g1']['carreras']
    for c in carreras:
        escribir(f'/carrera/{c["id"]}/', gen_carrera(d, c, slugs_uma, nombres_pj))
    lista = ''.join(f'<a href="/carrera/{e(c["id"])}/"><span>{e(c["nombre"])}<br><small class="sub">{e(c.get("hipodromo",""))}</small></span></a>' for c in carreras)
    escribir('/carrera/', pagina('Carreras G1: ganadores desde 1980 | Umadex', 'Las carreras G1 que sigue Umadex, con sus ganadores desde 1980, récords y las umas que las ganaron.',
                                 '/carrera/', f'<h1>Carreras G1</h1><div class="grid">{lista}</div>', migas=[('Carreras G1', None)]))
    hoy = datetime.date.today().isoformat()
    open(os.path.join(RAIZ, 'sitemap.xml'), 'w', encoding='utf8').write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
        ''.join(f'  <url><loc>{e(u)}</loc><lastmod>{hoy}</lastmod></url>\n' for u in urls) + '</urlset>\n')
    open(os.path.join(RAIZ, 'robots.txt'), 'w', encoding='utf8').write(f'User-agent: *\nAllow: /\n\nSitemap: {SITIO}/sitemap.xml\n')
    print(f'{len(orden)} personajes, {len(carreras)} carreras, {len(urls)} URLs en sitemap.xml')

if __name__ == '__main__':
    main()
