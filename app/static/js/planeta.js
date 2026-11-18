/* Planeta Verde — comportamiento de interfaz (solo presentación; no toca la lógica de negocio) */
(() => {
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];

  /* ---- Elementos que se revelan al entrar en pantalla (con escalonado) ---- */
  const AUTO = ".page-head, .filters, .vehicle, .panel, .kpi, .table-wrap, .news-card, .empty, .detail, .feature, .vs-card, .stat, .step, .article, .editor > *, .calc > *, .account > *, .fleet-card, .map-card, .conclusion";
  const targets = $$(AUTO).filter(e => !e.closest("[data-no-reveal]"));
  targets.forEach(e => e.setAttribute("data-reveal", ""));
  const parents = new Map();
  targets.forEach(e => {
    const p = e.parentElement, n = parents.get(p) || 0;
    e.style.setProperty("--d", Math.min(n, 8) * 70 + "ms"); parents.set(p, n + 1);
  });
  const show = e => { e.classList.add("in"); setTimeout(() => { e.removeAttribute("data-reveal"); e.classList.remove("in"); e.style.removeProperty("--d"); }, 1100 + parseInt(e.style.getPropertyValue("--d") || 0)); };
  if (reduce || !("IntersectionObserver" in window)) targets.forEach(show);
  else {
    const io = new IntersectionObserver(es => es.forEach(x => { if (x.isIntersecting) { show(x.target); io.unobserve(x.target); countUp(x.target); } }), { threshold: .12, rootMargin: "0px 0px -6% 0px" });
    targets.forEach(e => io.observe(e));
  }

  /* ---- Contadores animados: <b data-count="42" data-dec="0" data-pre="$"> ---- */
  function countUp(root) {
    $$("[data-count]", root).concat(root.matches?.("[data-count]") ? [root] : []).forEach(el => {
      if (el.dataset.done) return; el.dataset.done = 1;
      const end = parseFloat(el.dataset.count), dec = +(el.dataset.dec || 0), pre = el.dataset.pre || "", suf = el.dataset.suf || "";
      const fmt = v => pre + v.toLocaleString("es-CO", { minimumFractionDigits: dec, maximumFractionDigits: dec }) + suf;
      if (reduce || isNaN(end)) { el.textContent = fmt(end || 0); return; }
      const t0 = performance.now(), dur = 1100;
      const tick = t => { const k = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(1 - k, 3); el.textContent = fmt(end * e); if (k < 1) requestAnimationFrame(tick); };
      requestAnimationFrame(tick);
    });
  }
  $$("[data-count]").forEach(el => { if (!el.closest("[data-reveal]")) countUp(el.parentElement || el); });

  /* ---- Cabecera, progreso de lectura y botón "arriba" ---- */
  const header = $(".site-header"), bar = $(".progress"), top = $(".to-top");
  const onScroll = () => {
    const y = scrollY, h = document.documentElement.scrollHeight - innerHeight;
    header && header.classList.toggle("scrolled", y > 8);
    bar && (bar.style.transform = "scaleX(" + (h > 0 ? y / h : 0) + ")");
    top && top.classList.toggle("show", y > 600);
  };
  addEventListener("scroll", onScroll, { passive: true }); onScroll();
  top && top.addEventListener("click", () => scrollTo({ top: 0, behavior: reduce ? "auto" : "smooth" }));

  /* ---- Avisos: cerrar y desaparecer solos ---- */
  $$(".alert").forEach(a => {
    const close = () => { a.classList.add("out"); setTimeout(() => a.remove(), 320); };
    $(".alert-x", a)?.addEventListener("click", close);
    if (a.classList.contains("alert-success") || a.classList.contains("alert-info")) setTimeout(close, 6500);
  });

  /* ---- Ondas en botones y foco luminoso en tarjetas ---- */
  document.addEventListener("pointerdown", e => {
    const b = e.target.closest(".btn"); if (!b || reduce) return;
    const r = b.getBoundingClientRect(); b.style.setProperty("--rx", e.clientX - r.left + "px"); b.style.setProperty("--ry", e.clientY - r.top + "px");
    b.classList.remove("rip"); void b.offsetWidth; b.classList.add("rip");
  });
  if (!reduce && matchMedia("(hover:hover)").matches)
    document.addEventListener("pointermove", e => {
      const c = e.target.closest?.(".vehicle, .fleet-card, .vs-card, .news-card, .stat, .kpi");
      if (!c) return; const r = c.getBoundingClientRect();
      c.style.setProperty("--mx", e.clientX - r.left + "px"); c.style.setProperty("--my", e.clientY - r.top + "px");
    }, { passive: true });

  /* ---- Imágenes rotas: se sustituyen por la inicial (ver .media) ---- */
  $$("img[data-fallback]").forEach(img => {
    const fail = () => img.closest(".media")?.classList.add("broken");
    img.addEventListener("error", fail); if (img.complete && img.naturalWidth === 0) fail();
  });

  /* ---- Barras y anillos: se animan al revelarse ---- */
  $$(".track i, .donut").forEach(e => { e.style.setProperty("--to", e.style.width || ""); });
})();
