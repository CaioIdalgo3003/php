"""Calcula os cortes (remove pausas) a partir da transcrição do Whisper
e gera: cuts.json (trechos mantidos) e words.json (palavras no tempo editado)."""
import json, sys
src, out_dir = sys.argv[1], sys.argv[2]
d = json.load(open(src))
words = [w for s in d["segments"] for w in s["words"]]
GAP, PAD = 0.28, 0.09
keep = []
start = max(0, words[0]["start"] - 0.12)
for a, b in zip(words, words[1:]):
    if b["start"] - a["end"] > GAP:
        keep.append([start, a["end"] + PAD])
        start = b["start"] - PAD
keep.append([start, words[-1]["end"] + 0.45])
# tempo editado
def remap(t):
    acc = 0.0
    for s, e in keep:
        if t <= e:
            return acc + max(0.0, t - s)
        acc += e - s
    return acc
out_words = [{"w": w["word"].strip(), "s": round(remap(w["start"]), 3), "e": round(remap(w["end"]), 3),
              "src": round(w["start"], 3)} for w in words]
cut_points, acc = [], 0.0
for s, e in keep:
    acc += e - s
    cut_points.append(round(acc, 3))
json.dump({"keep": keep, "cuts": cut_points[:-1], "duration": round(acc, 3)}, open(f"{out_dir}/cuts.json", "w"), indent=1)
json.dump(out_words, open(f"{out_dir}/words.json", "w"), ensure_ascii=False, indent=0)
print(len(keep), "trechos; duração final", round(acc, 2), "s")
