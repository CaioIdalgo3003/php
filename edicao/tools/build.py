"""Gera index.html (composição HyperFrames) a partir de cuts.json e words.json.
Uso: python3 tools/build.py  (rodar dentro de edicao/)"""
import json, html, re

cuts = json.load(open("cuts.json"))
words = json.load(open("words.json"))
VID_DUR = 95.10
END_CARD = 2.2
TOTAL = round(VID_DUR + END_CARD, 2)

# ---------------------------------------------------------------- legendas
# correções de texto (gramática / transcrição) aplicadas às legendas
toks = [dict(w) for w in words]
i = 0
fixed = []
while i < len(toks):
    t = toks[i]
    w = t["w"]
    nxt = toks[i + 1]["w"] if i + 1 < len(toks) else ""
    if nxt in ("%", "%?") :
        t["w"] = w + nxt; t["e"] = toks[i + 1]["e"]; i += 2; fixed.append(t); continue
    if nxt == ",50":
        t["w"] = "R$ 57,50"; t["e"] = toks[i + 1]["e"]; i += 2; fixed.append(t); continue
    fixed.append(t); i += 1
toks = fixed
def at(word, near):
    """índice do token com texto `word` mais perto do tempo `near`"""
    c = [(abs(t["s"] - near), k) for k, t in enumerate(toks) if t["w"].strip(",.?").lower() == word.strip(",.?").lower()]
    return min(c)[1]
repl = {
    at("Meu", 68.4): "Minha",
    at("faturo", 45.1): "que faturo",
    at("mês", 39.5): "mesmo",
    at("150", 72.8): "R$ 1.150",
    at("mil", 72.6): "",
    at("100", 54.6): "R$ 100,",
    at("reais,", 55.0): "",
    at("115", 56.6): "R$ 115",
    at("50", 58.6): "R$ 50,",
    at("reais,", 59.7): "",
    at("mil", 70.3): "R$ 1.000,",
    at("reais,", 70.5): "",
    at("100,", 74.9): "R$ 100,",
    at("115", 75.4): "R$ 115",
    at("10", 18.4): "R$ 10",
    at("260", 22.9): "R$ 260",
    at("40", 29.9): "R$ 40",
    at("E", 4.18): "",
}
for k, v in repl.items():
    toks[k]["w"] = v
toks = [t for t in toks if t["w"]]
# primeira palavra perde o atraso do Whisper
KEY = re.compile(r"(R\$|\d|%|6x1|5x2)")
NEG = {"menos,", "menos", "cair", "ilusão", "diminuindo", "aumentar", "patrão"}

groups, cur = [], []
for t in toks:
    cur.append(t)
    txt = " ".join(x["w"] for x in cur)
    if t["w"].endswith((",", ".", "?")) or len(cur) >= 3 or len(txt) > 15:
        groups.append(cur); cur = []
if cur: groups.append(cur)

cap_html, cap_js = [], []
for gi, g in enumerate(groups):
    s = g[0]["s"]
    e = groups[gi + 1][0]["s"] if gi + 1 < len(groups) else VID_DUR
    e = min(e, g[-1]["e"] + 0.6)
    spans = []
    for wi, t in enumerate(g):
        word = html.escape(t["w"].rstrip(",").upper())
        cls = "w"
        if KEY.search(t["w"]): cls += " k"
        if t["w"].lower() in NEG: cls += " n"
        spans.append(f'<span class="{cls}" id="c{gi}_{wi}">{word}</span>')
        cap_js.append(f'tl.set("#c{gi}_{wi}",{{className:"{cls} on"}},{t["s"]:.2f});')
    cap_html.append(
        f'<div class="cap clip" id="cap{gi}" data-start="{s:.2f}" data-duration="{e - s:.2f}" data-track-index="5">{"".join(spans)}</div>')
    cap_js.append(f'tl.fromTo("#cap{gi}",{{y:24,scale:.92,opacity:0}},{{y:0,scale:1,opacity:1,duration:.16,ease:"back.out(2)"}},{s:.2f});')

# ---------------------------------------------------------------- câmera (cortes)
cam_js = []
scales = [1.0, 1.16, 1.06, 1.22]
cam_js.append('tl.set("#cam",{scale:1.0,x:0,y:0},0);')
for n, c in enumerate(cuts["cuts"]):
    sc = scales[(n + 1) % len(scales)]
    cam_js.append(f'tl.set("#cam",{{scale:{sc},y:{-40 if sc > 1.1 else 0}}},{c:.3f});')
# leve "respiração" contínua
cam_js.append('tl.fromTo("#drift",{scale:1.0},{scale:1.06,duration:%s,ease:"none"},0);' % VID_DUR)

# ---------------------------------------------------------------- SFX
sfx = []
def fx(name, t, vol=0.6, dur=1.0):
    n = len(sfx)
    sfx.append(f'<audio id="sfx{n}" class="clip" src="assets/sfx/{name}.wav" data-start="{t:.2f}" data-duration="{dur}" data-volume="{vol}" data-track-index="{9 + n % 3}"></audio>')

# ---------------------------------------------------------------- cenas
scenes = []
def scene(sid, s, e, inner, extra_cls=""):
    scenes.append(f'<section id="{sid}" class="scene clip {extra_cls}" data-start="{s:.2f}" data-duration="{e - s:.2f}" data-track-index="3">{inner}</section>')

S = {}  # tempos-chave
SVG_WALLET = '''<svg viewBox="0 0 200 160" class="ill"><rect x="10" y="30" width="170" height="115" rx="18" fill="#2b2b30" stroke="#FFD60A" stroke-width="5"/><path d="M30 30 L140 6 L152 30" fill="none" stroke="#FFD60A" stroke-width="5" stroke-linejoin="round"/><rect x="120" y="68" width="70" height="40" rx="12" fill="#1a1a1e" stroke="#FFD60A" stroke-width="5"/><circle cx="142" cy="88" r="7" fill="#FFD60A"/></svg>'''
SVG_STORE = '''<svg viewBox="0 0 220 190" class="ill"><rect x="20" y="70" width="180" height="110" rx="8" fill="#2b2b30" stroke="#fff" stroke-width="5"/><path d="M10 70 L30 20 H190 L210 70 Z" fill="#FF3B30" stroke="#fff" stroke-width="5" stroke-linejoin="round"/><path d="M46 20 L40 70 M82 20 L80 70 M118 20 L120 70 M154 20 L160 70" stroke="#fff" stroke-width="4"/><rect x="40" y="100" width="60" height="80" rx="4" fill="#1a1a1e" stroke="#fff" stroke-width="4"/><rect x="120" y="100" width="60" height="45" rx="4" fill="#FFD60A" opacity=".85"/><circle cx="90" cy="142" r="4" fill="#fff"/></svg>'''
SVG_PIZZA = '''<svg viewBox="0 0 200 200" class="ill"><circle cx="100" cy="100" r="88" fill="#E8A33D" stroke="#fff" stroke-width="5"/><circle cx="100" cy="100" r="72" fill="#D9452B"/><g fill="#F6D27A"><circle cx="70" cy="70" r="14"/><circle cx="130" cy="78" r="12"/><circle cx="96" cy="128" r="15"/><circle cx="140" cy="132" r="10"/><circle cx="60" cy="122" r="9"/></g><path d="M100 100 L100 12 M100 100 L176 144 M100 100 L24 144" stroke="#fff" stroke-width="4"/></svg>'''
SVG_CART = '''<svg viewBox="0 0 220 180" class="ill"><path d="M10 20 H45 L70 120 H180 L200 50 H55" fill="none" stroke="#fff" stroke-width="8" stroke-linejoin="round" stroke-linecap="round"/><rect x="72" y="58" width="30" height="42" rx="4" fill="#34C759"/><rect x="108" y="44" width="26" height="56" rx="4" fill="#FFD60A"/><rect x="140" y="64" width="34" height="36" rx="4" fill="#FF3B30"/><circle cx="85" cy="150" r="14" fill="#fff"/><circle cx="165" cy="150" r="14" fill="#fff"/></svg>'''
ICON_PEOPLE = '<svg viewBox="0 0 48 48"><circle cx="17" cy="15" r="7" fill="currentColor"/><circle cx="33" cy="17" r="6" fill="currentColor" opacity=".7"/><path d="M4 42c0-8 6-13 13-13s13 5 13 13z" fill="currentColor"/><path d="M28 42c0-6 2-10 6-11 6 0 10 5 10 11z" fill="currentColor" opacity=".7"/></svg>'
ICON_BOLT = '<svg viewBox="0 0 48 48"><path d="M27 3 L8 28 H22 L18 45 L40 18 H26 Z" fill="currentColor"/></svg>'
ICON_HOUSE = '<svg viewBox="0 0 48 48"><path d="M6 22 L24 6 L42 22 V42 H30 V30 H18 V42 H6 Z" fill="currentColor"/></svg>'

def days(n_off, ids):
    names = ["SEG", "TER", "QUA", "QUI", "SEX", "SÁB", "DOM"]
    out = []
    for k, nm in enumerate(names):
        off = k >= 7 - n_off
        out.append(f'<div class="day {"off" if off else "on"}" id="{ids}{k}"><b>{nm}</b><i>{"FOLGA" if off else "ABERTO"}</i></div>')
    return '<div class="week">' + "".join(out) + "</div>"

# 1) gancho
scene("s1", 0.0, 4.15, '''
<div class="kicker" id="s1k">URGENTE</div>
<h1 class="mega" id="s1t">FIM DA<br><span class="y">ESCALA 6x1</span></h1>
<div class="stamp" id="s1s">APROVADA</div>''', "top")
fx("whoosh", 0.0, 0.5); fx("impact", 2.34, 0.7)

# 2) seu bolso
scene("s2", 4.2, 13.25, f'''
<div class="card" id="s2c"><div class="row">{SVG_WALLET}<div>
<div class="lbl">QUEM PAGA A CONTA?</div>
<div class="big" id="s2a">O SEU BOLSO</div>
<div class="pill" id="s2b">VOCÊ, CONSUMIDOR FINAL</div>
<div class="pill red" id="s2d">NÃO O SEU PATRÃO</div></div></div></div>''', "top")
fx("whoosh", 8.95, 0.45); fx("pop", 10.0, 0.5); fx("pop", 12.42, 0.5)

# 3) empreendedor
scene("s3", 13.3, 19.45, f'''
<div class="card" id="s3c"><div class="lbl">EXEMPLO</div><div class="row">{SVG_STORE}<div>
<div class="big sm" id="s3a">SOU UM<br>EMPREENDEDOR</div>
<div class="money" id="s3m"><span class="cur">R$</span> <span id="s3n">0</span><small>/dia</small></div></div></div></div>''', "top")
fx("whoosh", 15.3, 0.45); fx("cash", 18.4, 0.6)

# 4) 6x1
scene("s4", 19.5, 24.25, f'''
<div class="card" id="s4c"><div class="lbl">ESCALA <span class="y">6x1</span></div>{days(1, "d1_")}
<div class="calc"><span>R$ 10 mil × 26 dias</span><span class="eq">=</span></div>
<div class="money g" id="s4m"><span class="cur">R$</span> <span id="s4n">0</span><small>/mês</small></div></div>''', "top")
fx("whoosh", 19.5, 0.4); fx("cash", 22.9, 0.6)

# 5) 5x2
scene("s5", 24.3, 31.0, f'''
<div class="card" id="s5c"><div class="lbl">AGORA: ESCALA <span class="y">5x2</span></div>{days(2, "d2_")}
<div class="calc"><span id="s5x">−4 dias por mês</span></div>
<div class="money r" id="s5m"><span>−R$</span> <span>40.000</span><small>/mês</small></div></div>''', "top")
fx("whoosh", 24.3, 0.4); fx("impact", 26.24, 0.45); fx("impact", 29.92, 0.6)

# 6) 15%  (tela cheia)
scene("s6", 31.05, 35.72, '''
<div class="full"><div class="donut"><svg viewBox="0 0 200 200"><circle cx="100" cy="100" r="80" class="ring"/>
<circle cx="100" cy="100" r="80" class="slice" id="s6p" pathLength="100" stroke-dasharray="0 100"/></svg>
<div class="dlabel"><div id="s6n" class="pct">0%</div><small>do faturamento</small></div></div>
<div class="sub">R$ 40 mil de R$ 260 mil</div></div>''', "dim")
fx("whoosh", 31.05, 0.45); fx("impact", 35.0, 0.6)

# 7) custos iguais
scene("s7", 35.75, 45.55, f'''
<div class="card" id="s7c"><div class="lbl">MAS OS CUSTOS CONTINUAM</div>
<div class="cost" id="s7a"><span class="ic">{ICON_PEOPLE}</span>Folha de pagamento<em>=</em></div>
<div class="cost" id="s7b"><span class="ic">{ICON_BOLT}</span>Energia<em>=</em></div>
<div class="cost" id="s7d"><span class="ic">{ICON_HOUSE}</span>Aluguel<em>=</em></div>
<div class="big y sm" id="s7e">TUDO IGUAL</div>
<div class="pill red" id="s7f">↓ SÓ O FATURAMENTO CAIU</div></div>''', "top")
fx("pop", 37.94, 0.5); fx("pop", 41.08, 0.5); fx("pop", 41.72, 0.5); fx("impact", 42.32, 0.5); fx("whoosh", 44.9, 0.4)

# 8) repasse 15%
scene("s8", 45.6, 52.2, '''
<div class="card" id="s8c"><div class="lbl">DE ONDE SAEM OS 15%?</div>
<div class="flow"><div class="box" id="s8a">CUSTO<br><b class="r">+15%</b></div><div class="arrow" id="s8r">→</div>
<div class="tag" id="s8b"><span>PREÇO<br>FINAL</span><b>+15%</b></div></div></div>''', "top")
fx("whoosh", 45.6, 0.4); fx("impact", 49.16, 0.55)

# 9) exemplos de preço
def price_row(rid, old, new):
    return f'<div class="prow" id="{rid}"><div class="ptag old">{old}</div><div class="parr">→</div><div class="ptag new" id="{rid}n">{new}</div></div>'
scene("s9", 52.25, 62.4, f'''
<div class="card" id="s9c"><div class="lbl">NA PRÁTICA (+15%)</div>
{price_row("s9a", "R$ 100", "R$ 115")}
{price_row("s9b", "R$ 50", "R$ 57,50")}</div>''', "top")
fx("pop", 54.62, 0.5); fx("cash", 56.6, 0.6); fx("pop", 58.58, 0.5); fx("cash", 60.4, 0.6)

# 10) pizza + compra do mês
scene("s10", 62.45, 76.75, f'''
<div class="card" id="s10c"><div class="lbl">NO SEU DIA A DIA</div>
<div class="duo"><div class="item" id="s10p">{SVG_PIZZA}<div class="iname">PIZZA</div><div class="iprice" id="s10pp">R$ 100</div></div>
<div class="item" id="s10m">{SVG_CART}<div class="iname">COMPRA DO MÊS</div><div class="iprice" id="s10mp">R$ 1.000</div></div></div></div>''', "top")
fx("whoosh", 62.45, 0.4); fx("pop", 65.94, 0.5); fx("pop", 67.62, 0.5); fx("cash", 72.6, 0.6); fx("cash", 75.36, 0.6)

# 11) ilusão / vitória?
scene("s11", 76.8, 83.9, '''
<div class="full low"><div class="mega" id="s11a">ILUSÃO</div>
<div class="victory" id="s11b">"VITÓRIA"<span class="q">?</span></div></div>''', "dim")
fx("whoosh", 78.3, 0.45); fx("impact", 82.6, 0.65)

# 12) poder de compra
scene("s12", 83.95, VID_DUR, '''
<div class="card" id="s12c"><div class="lbl">O QUE ACONTECE COM VOCÊ</div>
<svg viewBox="0 0 900 380" class="chart">
<line x1="40" y1="340" x2="880" y2="340" class="axis"/>
<path id="s12up" d="M40 260 C 300 250, 520 170, 860 60" class="lp" pathLength="100" stroke-dasharray="0 100"/>
<path id="s12fl" d="M40 260 L 860 258" class="lf" pathLength="100" stroke-dasharray="0 100"/>
<text x="700" y="44" class="tr" id="s12t1">PREÇOS ↑</text>
<text x="60" y="230" class="tw" id="s12t2">SEU SALÁRIO =</text></svg>
<div class="big r sm" id="s12b">PODER DE COMPRA ↓</div></div>''', "top")
fx("whoosh", 83.95, 0.4); fx("impact", 89.42, 0.6); fx("pop", 92.0, 0.5); fx("pop", 93.22, 0.5)

# 13) cartão final
scene("s13", VID_DUR - 0.3, TOTAL, '''
<div class="full end"><div class="kicker">E VOCÊ?</div><h1 class="mega">CONCORDA<span class="y">?</span></h1>
<div class="sub">Comenta aqui embaixo 👇</div></div>''', "black")
fx("impact", VID_DUR, 0.5, 1.5)

# ---------------------------------------------------------------- animações das cenas
A = r'''
const IN = (sel,t,from={y:40,opacity:0})=>tl.fromTo(sel,from,{y:0,x:0,opacity:1,scale:1,duration:.35,ease:"power3.out"},t);
const POP = (sel,t)=>tl.fromTo(sel,{scale:.4,opacity:0},{scale:1,opacity:1,duration:.32,ease:"back.out(2.2)"},t);
const OUT = (sel,t)=>tl.to(sel,{opacity:0,y:-30,duration:.22,ease:"power2.in"},t);
const COUNT=(sel,from,to,t,d,fmt)=>{const o={v:from};tl.to(o,{v:to,duration:d,ease:"power2.out",onUpdate:()=>{document.querySelector(sel).textContent=fmt(o.v)}},t);tl.set(sel,{textContent:fmt(from)},Math.max(0,t-0.01));};
const BR = v=>Math.round(v).toLocaleString("pt-BR");
// 1
IN("#s1k",0.05,{y:-20,opacity:0}); tl.fromTo("#s1t",{scale:1.4,opacity:0},{scale:1,opacity:1,duration:.45,ease:"expo.out"},0.15);
tl.fromTo("#s1s",{scale:3,opacity:0,rotation:-14},{scale:1,opacity:1,rotation:-8,duration:.28,ease:"power4.in"},2.1);
tl.fromTo("#flash",{opacity:.0},{opacity:.55,duration:.05},2.36); tl.to("#flash",{opacity:0,duration:.35},2.41);
OUT("#s1t,#s1s,#s1k",3.95);
// 2
IN("#s2c",4.3); POP("#s2a",9.1); POP("#s2b",9.95); POP("#s2d",12.4); OUT("#s2c",13.05);
// 3
IN("#s3c",13.35); POP("#s3a",15.4); POP("#s3m",18.25); COUNT("#s3n",0,10000,18.3,.8,BR); OUT("#s3c",19.25);
// 4
IN("#s4c",19.55); tl.fromTo("#d1_0,#d1_1,#d1_2,#d1_3,#d1_4,#d1_5,#d1_6",{scale:.5,opacity:0},{scale:1,opacity:1,duration:.25,stagger:.07,ease:"back.out(2)"},20.7);
POP("#s4m",22.8); COUNT("#s4n",0,260000,22.85,1.0,BR); OUT("#s4c",24.05);
// 5
IN("#s5c",24.35); tl.fromTo("#d2_0,#d2_1,#d2_2,#d2_3,#d2_4",{opacity:0},{opacity:1,duration:.2,stagger:.05},24.5);
tl.fromTo("#d2_5",{opacity:0,scale:1.6},{opacity:1,scale:1,duration:.3,ease:"back.out(2)"},26.2);
tl.fromTo("#d2_6",{opacity:0},{opacity:1,duration:.2},24.8);
POP("#s5x",27.95); tl.fromTo("#s5m",{scale:2.2,opacity:0},{scale:1,opacity:1,duration:.3,ease:"power4.in"},29.65);
tl.to("#s5c",{x:-14,duration:.04,yoyo:true,repeat:5},29.95); OUT("#s5c",30.8);
// 6
tl.fromTo("#s6 .donut",{scale:.6,opacity:0},{scale:1,opacity:1,duration:.4,ease:"back.out(1.6)"},31.1);
tl.to("#s6p",{attr:{"stroke-dasharray":"15.4 100"},duration:1.1,ease:"power2.inOut"},34.0);
COUNT("#s6n",0,15,34.0,1.1,v=>Math.round(v)+"%"); IN("#s6 .sub",33.9); OUT("#s6 .full",35.5);
// 7
IN("#s7c",35.8); IN("#s7a",37.9,{x:-60,opacity:0}); IN("#s7b",41.0,{x:-60,opacity:0}); IN("#s7d",41.66,{x:-60,opacity:0});
POP("#s7e",42.3); POP("#s7f",44.95); OUT("#s7c",45.4);
// 8
IN("#s8c",45.65); POP("#s8a",46.9); tl.fromTo("#s8r",{x:-40,opacity:0},{x:0,opacity:1,duration:.3},48.6); POP("#s8b",49.1);
tl.to("#s8b",{rotation:-4,scale:1.06,duration:.25,yoyo:true,repeat:1},50.8); OUT("#s8c",52.0);
// 9
IN("#s9c",52.3); IN("#s9a",54.5); tl.set("#s9an",{opacity:0},52.3); POP("#s9an",56.5);
IN("#s9b",58.5); tl.set("#s9bn",{opacity:0},52.3); POP("#s9bn",60.3); OUT("#s9c",62.2);
// 10
IN("#s10c",62.5); POP("#s10p",65.85); POP("#s10m",67.55);
tl.to("#s10mp",{scale:1.25,color:"#FF3B30",duration:.2},72.55); tl.set("#s10mp",{textContent:"R$ 1.150"},72.6); tl.to("#s10mp",{scale:1,duration:.25},72.8);
tl.to("#s10pp",{scale:1.25,color:"#FF3B30",duration:.2},75.3); tl.set("#s10pp",{textContent:"R$ 115"},75.36); tl.to("#s10pp",{scale:1,duration:.25},75.56);
OUT("#s10c",76.55);
// 11
tl.fromTo("#s11a",{scale:1.8,opacity:0},{scale:1,opacity:1,duration:.6,ease:"expo.out"},78.35);
tl.to("#s11a",{opacity:.25,duration:.4},81.9);
tl.fromTo("#s11b",{scale:2.4,opacity:0},{scale:1,opacity:1,duration:.3,ease:"power4.in"},82.35);
tl.to("#s11b",{x:10,duration:.04,yoyo:true,repeat:7},82.65); tl.to("#s11b .q",{color:"#FF3B30",scale:1.3,duration:.2},82.7);
OUT("#s11 .full",83.7);
// 12
IN("#s12c",84.0); tl.to("#s12fl",{attr:{"stroke-dasharray":"100 0"},duration:1.4,ease:"none"},85.0);
tl.to("#s12up",{attr:{"stroke-dasharray":"100 0"},duration:1.6,ease:"power2.in"},90.6);
IN("#s12t1",92.0,{y:20,opacity:0}); IN("#s12t2",93.2,{y:20,opacity:0}); POP("#s12b",89.4);
OUT("#s12c",%(VEND)s);
// 13
tl.fromTo("#s13 .kicker",{opacity:0,y:20},{opacity:1,y:0,duration:.3},%(VEND)s+0.05);
tl.fromTo("#s13 .mega",{scale:1.3,opacity:0},{scale:1,opacity:1,duration:.45,ease:"expo.out"},%(VEND)s+0.15);
tl.fromTo("#s13 .sub",{opacity:0},{opacity:1,duration:.3},%(VEND)s+0.6);
// vídeo: escurece nas cenas de tela cheia e some no final
tl.to("#shade",{opacity:.72,duration:.3},31.0); tl.to("#shade",{opacity:0,duration:.3},35.6);
tl.to("#shade",{opacity:.6,duration:.3},78.2); tl.to("#shade",{opacity:0,duration:.3},83.7);
tl.to("#shade",{opacity:1,duration:.5},%(VEND)s-0.3);
'''.replace("%(VEND)s", f"{VID_DUR - 0.25:.2f}")

page = f'''<!doctype html>
<html lang="pt-BR" data-resolution="portrait">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<link rel="stylesheet" href="assets/fonts.css" />
<script src="assets/vendor/gsap.min.js"></script>
<style>
:root{{--ground:#000;--ink:#fff;--y:#FFD60A;--r:#FF3B30;--g:#34C759;--panel:rgba(12,12,16,.78);
--font-display:'Anton',sans-serif;--font-ui:'Inter',Arial,sans-serif;}}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:1080px;height:1920px;overflow:hidden;background:var(--ground)}}
#root{{position:relative;width:100%;height:100%;overflow:hidden;font-family:var(--font-ui);color:var(--ink)}}
.clip{{position:absolute;inset:0}}
#cam{{position:absolute;inset:0;transform-origin:50% 42%}}
#drift{{position:absolute;inset:0;transform-origin:50% 45%}}
#vid{{width:1080px;height:1920px;object-fit:cover}}
#shade{{position:absolute;inset:0;background:radial-gradient(ellipse at 50% 45%,rgba(0,0,0,.55),rgba(0,0,0,.95));opacity:0}}
#vign{{position:absolute;inset:0;pointer-events:none;background:
 linear-gradient(180deg,rgba(0,0,0,.55) 0%,rgba(0,0,0,0) 22%,rgba(0,0,0,0) 62%,rgba(0,0,0,.7) 100%)}}
#bars{{position:absolute;inset:0;pointer-events:none;border-top:46px solid #000;border-bottom:46px solid #000}}
#flash{{position:absolute;inset:0;background:#fff;opacity:0}}
.y{{color:var(--y)}} .r{{color:var(--r)}} .g{{color:var(--g)}}
.scene.top{{display:flex;flex-direction:column;align-items:center;padding-top:150px}}
.scene.dim .full,.scene.black .full{{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:40px}}
.scene.black{{background:#000}}
.kicker{{font:900 34px/1 var(--font-ui);letter-spacing:.32em;color:var(--r);background:rgba(255,59,48,.12);border:2px solid var(--r);padding:12px 22px;border-radius:10px}}
.mega{{font:400 150px/0.95 var(--font-display);text-align:center;text-transform:uppercase;letter-spacing:2px;text-shadow:0 10px 40px rgba(0,0,0,.8);margin-top:24px}}
.stamp{{margin-top:34px;font:400 96px/1 var(--font-display);color:var(--r);border:10px solid var(--r);padding:6px 30px 0;border-radius:14px;transform:rotate(-8deg);letter-spacing:6px;background:rgba(0,0,0,.35)}}
.card{{width:960px;background:var(--panel);border:1.5px solid rgba(255,255,255,.14);border-radius:40px;padding:44px 48px;
 box-shadow:0 30px 80px rgba(0,0,0,.6);backdrop-filter:blur(6px)}}
.lbl{{font:700 30px/1 var(--font-ui);letter-spacing:.2em;color:rgba(255,255,255,.65);margin-bottom:28px;text-transform:uppercase}}
.row{{display:flex;align-items:center;gap:40px}}
.ill{{width:250px;flex:none;filter:drop-shadow(0 12px 24px rgba(0,0,0,.5))}}
.big{{font:400 92px/1 var(--font-display);text-transform:uppercase;letter-spacing:1px}}
.big.sm{{font-size:76px;margin-top:10px}}
.pill{{display:inline-block;margin-top:18px;font:800 30px/1 var(--font-ui);background:var(--y);color:#000;padding:14px 22px;border-radius:999px}}
.pill.red{{background:var(--r);color:#fff}}
.money{{margin-top:20px;font:400 104px/1 var(--font-display);color:var(--g);white-space:nowrap}}
.money .cur{{font-size:62px}} .money small{{font:700 32px var(--font-ui);color:rgba(255,255,255,.7);margin-left:10px}}
.money.r{{color:var(--r)}}
.week{{display:grid;grid-template-columns:repeat(7,1fr);gap:12px}}
.day{{border-radius:18px;padding:18px 0;text-align:center;background:rgba(52,199,89,.18);border:2px solid var(--g)}}
.day b{{display:block;font:900 28px/1 var(--font-ui)}} .day i{{display:block;font:700 15px/1 var(--font-ui);margin-top:10px;font-style:normal;letter-spacing:.06em;color:var(--g)}}
.day.off{{background:rgba(255,255,255,.06);border-color:rgba(255,255,255,.25)}} .day.off i{{color:rgba(255,255,255,.55)}}
.calc{{margin-top:30px;font:700 40px/1 var(--font-ui);color:rgba(255,255,255,.85);display:flex;gap:18px}}
.donut{{position:relative;width:640px;height:640px}}
.donut svg{{width:100%;height:100%;transform:rotate(-90deg)}}
.ring{{fill:none;stroke:rgba(255,255,255,.14);stroke-width:30}}
.slice{{fill:none;stroke:var(--r);stroke-width:30;stroke-linecap:round}}
.dlabel{{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center}}
.pct{{font:400 210px/1 var(--font-display);color:var(--r)}}
.dlabel small{{font:700 34px var(--font-ui);color:rgba(255,255,255,.7);letter-spacing:.08em}}
.sub{{font:700 44px var(--font-ui);color:rgba(255,255,255,.85)}}
.cost{{display:flex;align-items:center;gap:24px;font:700 50px/1 var(--font-ui);padding:20px 0;border-bottom:1.5px solid rgba(255,255,255,.1)}}
.cost .ic{{width:72px;height:72px;border-radius:18px;background:rgba(255,214,10,.15);color:var(--y);display:grid;place-items:center}}
.cost .ic svg{{width:44px;height:44px}}
.cost em{{margin-left:auto;font:400 64px var(--font-display);color:var(--y);font-style:normal}}
.flow{{display:flex;align-items:center;justify-content:space-between}}
.box{{font:400 70px/1.05 var(--font-display);text-align:center;border:3px dashed rgba(255,255,255,.4);border-radius:24px;padding:28px 34px}}
.arrow{{font:400 120px var(--font-display);color:var(--y)}}
.tag{{display:flex;flex-direction:column;align-items:center;background:var(--y);color:#000;border-radius:24px 24px 24px 24px;padding:24px 34px;font:400 52px/1 var(--font-display);text-align:center;position:relative}}
.tag b{{font-size:100px;color:var(--r);font-weight:400}}
.prow{{display:flex;align-items:center;justify-content:space-between;margin:18px 0}}
.ptag{{font:400 100px/1 var(--font-display);padding:16px 30px;border-radius:20px}}
.ptag.old{{color:rgba(255,255,255,.55);text-decoration:line-through;text-decoration-thickness:6px;text-decoration-color:var(--r)}}
.ptag.new{{background:var(--r);color:#fff}}
.parr{{font:400 90px var(--font-display);color:var(--y)}}
.duo{{display:flex;justify-content:space-around;gap:30px}}
.item{{display:flex;flex-direction:column;align-items:center;gap:14px}}
.item .ill{{width:230px}}
.iname{{font:800 30px var(--font-ui);letter-spacing:.12em;color:rgba(255,255,255,.75)}}
.iprice{{font:400 88px/1 var(--font-display);color:var(--y)}}
.full.low{{justify-content:flex-start;padding-top:330px}}
.victory{{font:400 140px/1 var(--font-display);color:var(--g);text-transform:uppercase}}
.victory .q{{display:inline-block;color:#fff}}
.chart{{width:100%;height:auto}}
.axis{{stroke:rgba(255,255,255,.3);stroke-width:3}}
.lp{{fill:none;stroke:var(--r);stroke-width:12;stroke-linecap:round}}
.lf{{fill:none;stroke:rgba(255,255,255,.85);stroke-width:10;stroke-linecap:round}}
.tr{{fill:var(--r);font:400 54px var(--font-display)}} .tw{{fill:#fff;font:400 46px var(--font-display)}}
.end .sub{{font-size:46px}}
.cap{{top:auto;bottom:300px;height:auto;display:flex;flex-wrap:wrap;justify-content:center;gap:0 22px;padding:0 70px;
 font:400 104px/1.08 var(--font-display);text-transform:uppercase;letter-spacing:1px;text-align:center}}
.cap .w{{color:#fff;-webkit-text-stroke:3px rgba(0,0,0,.85);paint-order:stroke fill;text-shadow:0 8px 24px rgba(0,0,0,.9);opacity:.55;display:inline-block}}
.cap .w.on{{opacity:1}}
.cap .w.k.on{{color:var(--y)}}
.cap .w.n.on{{color:var(--r)}}
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="1080" data-height="1920">
<div id="cam"><div id="drift">
<video id="vid" class="clip" src="media/edited.mp4" data-start="0" data-duration="{VID_DUR}" data-has-audio="true" data-volume="1" data-track-index="0" playsinline></video>
</div></div>
<div id="shade"></div>
<div id="vign"></div>
{"".join(scenes)}
{"".join(cap_html)}
<div id="flash"></div>
<div id="bars"></div>
<audio id="music" class="clip" src="assets/music_bed.mp3" data-start="0" data-duration="{TOTAL}" data-volume="0.16" data-fade-in="1" data-fade-out="2" data-track-index="8"></audio>
{"".join(sfx)}
</div>
<script>
const tl = gsap.timeline({{ paused: true }});
{"".join(cam_js)}
{A}
{"".join(cap_js)}
window.__timelines = window.__timelines || {{}};
window.__timelines["main"] = tl;
tl.seek(0);
</script>
</body>
</html>
'''
open("index.html", "w").write(page)
print("index.html ok —", len(groups), "legendas,", len(scenes), "cenas, duração", TOTAL)
