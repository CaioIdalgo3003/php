# Edição — "Fim da escala 6x1"

Projeto [HyperFrames](https://hyperframes.heygen.com) gerado a partir do vídeo vertical gravado no carro.

## Pipeline
1. **Cor** (FFmpeg): curvas para levantar os meios-tons, pretos densos, leve tom quente na pele,
   redução de ruído, nitidez e vinheta → `graded.mp4` (filtro em `tools/grade_filter.txt`).
2. **Transcrição** (Whisper `small`, pt, timestamps por palavra).
3. **Cortes** (`tools/cuts.py`): remove pausas > 0,28 s (jump cuts) → `cuts.json`, `words.json`.
4. **Montagem** (FFmpeg, `tools/edit_filter.txt`): concatena os trechos, compensa o brilho por trecho
   (`gamma.json`) e trata o áudio (passa-alta, redução de ruído, EQ de voz, compressor, -16 LUFS)
   → `media/edited.mp4`.
5. **Composição** (`tools/build.py` → `index.html`): zoom alternado a cada corte, 12 cenas com
   ilustrações SVG e gráficos animados, legendas palavra a palavra (com correções de texto),
   trilha ambiente e efeitos sonoros sintetizados.
6. **Render**: `npx hyperframes render -q delivery -o renders/fim-escala-6x1.mp4`

Os vídeos (`media/`, `renders/`) não vão para o git por causa do tamanho.
