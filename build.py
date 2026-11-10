from html import escape as esc
from pathlib import Path
import re

ROOT = Path(__file__).parent
REF = re.compile(r'(\[[RACS]\d{2}\]|\*\*[^*]+\*\*)')
EXPR = re.compile(r'([A-Za-zΑ-ωℓ][A-Za-zΑ-ωℓ0-9]*|[∑∏])_\{([^}]+)\}(?:\^\{([^}]+)\})?|([A-Za-zΑ-ωℓ][A-Za-zΑ-ωℓ0-9]*)\^\{([^}]+)\}')
sections = {
    2:'methodology', 3:'market-rules', 4:'decision-clock', 5:'data', 6:'features',
    7:'day-ahead', 8:'real-time', 9:'spread', 10:'scenarios', 11:'settlement',
    12:'storage-model', 13:'market-replay', 14:'bidding', 15:'operations',
    16:'backtest', 17:'implementation', 18:'policy-sources', 19:'literature',
    20:'code-and-data', 21:'gradient-engine',
}
groups = [
    (2, 4, '研究与市场'), (5, 10, '预测算法'), (11, 15, '储能报价'),
    (16, 17, '验证与实施'), (18, 20, '来源与复现'), (21, 21, '公众号补充'),
]

def rich(value):
    out = []
    for part in REF.split(value):
        if REF.fullmatch(part):
            if part.startswith('['):
                ident = part[1:-1]
                out.append(f'<a class="citation" href="#ref-{ident}" aria-label="来源 {ident}">{ident}</a>')
            else:
                out.append(f'<strong>{esc(part[2:-2])}</strong>')
        else:
            out.append(esc(part))
    return ''.join(out)

def math(value):
    out, pos = [], 0
    for match in EXPR.finditer(value):
        out.append(esc(value[pos:match.start()]))
        base, sub, sup, base2, sup2 = match.groups()
        out.append(f'<var>{esc(base or base2)}</var>')
        if sub:
            out.append(f'<sub>{esc(sub)}</sub>')
        if sup or sup2:
            out.append(f'<sup>{esc(sup or sup2)}</sup>')
        pos = match.end()
    out.append(esc(value[pos:]))
    return ''.join(out).replace('  ', ' &nbsp;')

def table(lines):
    header, *body = [line.split(' | ') for line in lines]
    head = ''.join(f'<th scope="col">{rich(value)}</th>' for value in header)
    rows = []
    for row in body:
        cells = ''.join(f'<td>{rich(value)}</td>' for value in row)
        rows.append(f'<tr>{cells}</tr>')
    return f'<div class="table-wrap" tabindex="0" role="region" aria-label="{esc(header[0])}对照表"><table><thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'

def source(value):
    ident, label, url, note = value.split(' | ', 3)
    title = esc(label)
    if url:
        title = (f'<a href="{esc(url, quote=True)}" target="_blank" rel="noopener noreferrer">'
                 f'{title} <span aria-hidden="true">↗</span></a>')
    else:
        title = f'<strong>{title}</strong>'
    return (f'<li class="source" id="ref-{ident}"><span class="source-id">{ident}</span>'
            f'<div>{title}<p>{esc(note)}</p></div></li>')

def parse():
    blocks = re.split(r'\n=== ', (ROOT/'report.txt').read_text(encoding='utf-8'))[1:]
    result = []
    for block in blocks:
        heading, *body = block.splitlines()
        label, title = heading.split(' | ', 1)
        n, title = title.split(' ', 1)
        result.append((int(n), label, title, body))
    return result

def render_body(body):
    blocks = []
    i = 0
    while i < len(body):
        line = body[i]
        i += 1
        if not line.strip():
            continue
        if line.startswith('TABLE '):
            end = body.index('END', i)
            blocks.append(table(body[i:end]))
            i = end + 1
        elif line.startswith('## '):
            blocks.append(f'<h3>{esc(line[3:])}</h3>')
        elif line.startswith('SMALL '):
            blocks.append(f'<p class="note">{rich(line[6:])}</p>')
        elif line.startswith(('EQ ', 'CODE ', 'REF ')):
            kind = line.split(' ', 1)[0]
            lines = [line[len(kind)+1:]]
            while i < len(body) and body[i].startswith(f'{kind} '):
                lines.append(body[i][len(kind)+1:])
                i += 1
            if kind == 'EQ':
                equations = ''.join(f'<div>{math(item.strip())}</div>' for item in lines)
                blocks.append(f'<div class="formula" tabindex="0" aria-label="计算公式">{equations}</div>')
            elif kind == 'CODE':
                blocks.append('<div class="code-wrap"><button class="copy" type="button" hidden>复制伪代码</button>'
                              '<pre tabindex="0"><code>' + esc('\n'.join(lines)) + '</code></pre></div>')
            else:
                blocks.append(f'<ul class="sources">{"".join(source(item) for item in lines)}</ul>')
        elif re.match(r'^\d+\. ', line):
            items = [line.split('. ', 1)[1]]
            while i < len(body) and re.match(r'^\d+\. ', body[i]):
                items.append(body[i].split('. ', 1)[1])
                i += 1
            blocks.append(f'<ol class="steps">{"".join(f"<li>{rich(item)}</li>" for item in items)}</ol>')
        else:
            blocks.append(f'<p>{rich(line)}</p>')
    return '\n'.join(blocks)

def make_nav(chapters):
    out = []
    for start, end, label in groups:
        items = [f'<a href="#{sections[n]}"><span>{n:02}</span>{esc(title)}</a>'
                 for n, _, title, _ in chapters if start <= n <= end]
        out.append(f'<div class="nav-group"><p>{label}</p>{"".join(items)}</div>')
    return '\n'.join(out)

chapters = parse()
calculator = (ROOT/'calculator.html').read_text(encoding='utf-8')
article = []
for n, label, title, body in chapters:
    slug = sections[n]
    article.append(f'<section class="chapter" id="{slug}" data-chapter="{n:02}" aria-labelledby="{slug}-title">'
                   f'<div class="chapter-label"><span>{n:02}</span>{esc(label[3:])}</div>'
                   f'<h2 id="{slug}-title">{esc(title)}</h2>{render_body(body)}'
                   f'{calculator if n == 11 else ""}</section>')
template = (ROOT/'template.html').read_text(encoding='utf-8')
source_count = sum(line.startswith('REF ') for _, _, _, body in chapters for line in body)
html = (template.replace('{{SOURCE_COUNT}}', str(source_count))
        .replace('<!-- NAV -->', make_nav(chapters))
        .replace('<!-- REPORT -->', '\n'.join(article)))
(ROOT/'docs'/'index.html').write_text(html,encoding='utf-8')
