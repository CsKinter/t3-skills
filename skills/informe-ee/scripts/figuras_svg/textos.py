"""Lista los textos de un volcado de formas como puntos de anclaje (x según alineación, y al centro) para escribir specs."""
import json, sys
for f in json.load(open(sys.argv[1], encoding='utf-8')):
    for i, s in enumerate(f['formas']):
        if not s.get('txt'): continue
        p = s['txt'][0]; jc = p['jc'] or 'left'
        x = {'center': s['x'] + s['w'] / 2, 'left': s['x'], 'right': s['x'] + s['w']}.get(jc, s['x'])
        st = p['runs'][0][1] if p['runs'] else {}
        t = '\n'.join(''.join(r[0] for r in q['runs']) for q in s['txt'])
        mix = any(r[1] != st for q in s['txt'] for r in q['runs'])
        print(i, f'[{x:.3f},{s["y"] + s["h"] / 2:.3f}]', jc, st.get('pt'), st.get('c'), 'b' if st.get('b') else '', 'MIX' if mix else '', repr(t), ('fill=' + str(s.get('fill'))) if s.get('fill') else '')
