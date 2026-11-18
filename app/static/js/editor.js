/* Editor de noticias: vista previa en vivo, contador, arrastrar y soltar imagen (solo presentación) */
(() => {
  const $ = id => document.getElementById(id);
  const titulo = $('titulo'), cat = $('categoria'), autor = $('autor'), vistas = $('vistas'), cont = $('contenido'), img = $('imagen');
  if (!titulo) return;
  const pv = { t: $('pv-titulo'), c: $('pv-categoria'), a: $('pv-autor'), v: $('pv-vistas'), x: $('pv-contenido'), img: $('pv-img'), mono: $('pv-mono') };
  const draw = () => {
    const t = titulo.value.trim();
    pv.t.textContent = t || 'Título de la noticia';
    pv.c.textContent = cat.value ? cat.options[cat.selectedIndex].text : 'Categoría';
    pv.a.textContent = autor.value.trim() || 'Autor';
    pv.v.textContent = vistas.value || '0';
    const body = cont.value.trim();
    pv.x.textContent = body ? body.slice(0, 150) + (body.length > 150 ? '...' : '') : 'Aquí se verá una vista previa del contenido...';
    pv.mono.textContent = (t[0] || 'N').toUpperCase();
    const n = $('contador'); if (n) n.textContent = cont.value.length.toLocaleString('es-CO') + ' caracteres';
  };
  [titulo, cat, autor, vistas, cont].forEach(e => e.addEventListener('input', draw)); cat.addEventListener('change', draw); draw();

  const zone = $('dropzone'), label = $('fileName');
  const setFile = f => {
    if (!f) return;
    label.textContent = f.name;
    if (!f.type.startsWith('image/')) return;
    const r = new FileReader(); r.onload = () => { pv.img.src = r.result; pv.img.hidden = false; pv.mono.parentElement.classList.remove('broken'); pv.mono.style.display = 'none'; }; r.readAsDataURL(f);
  };
  img.addEventListener('change', () => setFile(img.files[0]));
  ['dragenter', 'dragover'].forEach(ev => zone.addEventListener(ev, e => { e.preventDefault(); zone.classList.add('over'); }));
  ['dragleave', 'drop'].forEach(ev => zone.addEventListener(ev, () => zone.classList.remove('over')));
  zone.addEventListener('drop', e => { e.preventDefault(); if (e.dataTransfer.files.length) { img.files = e.dataTransfer.files; setFile(img.files[0]); } });
})();
