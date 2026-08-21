// ===== POS: altura dinámica =====
(function () {
  function ajustarAltura() {
    var cont = document.querySelector('.pos-fullscreen');
    if (!cont) return;
    var rect = cont.getBoundingClientRect();
    cont.style.height = (window.innerHeight - rect.top - 10) + 'px';
  }
  window.addEventListener('resize', ajustarAltura);
  document.addEventListener('DOMContentLoaded', ajustarAltura);
  ajustarAltura();
})();

// ===== POS: navegación y edición del ticket =====
(function () {
  var sel = -1;
  var buffer = '';
  var bufferTimer = null;

  function lineas() {
    return document.querySelectorAll('.ticket-scroll .ticket-linea[data-indice], .ticket-lista .ticket-linea[data-indice]');
  }
  function navegar(dir) {
    var ls = lineas();
    if (!ls.length) return;
    ls.forEach(function (l) { l.classList.remove('seleccionada'); });
    sel = dir === 'down' ? (sel + 1) % ls.length : (sel <= 0 ? ls.length - 1 : sel - 1);
    ls[sel].classList.add('seleccionada');
    ls[sel].scrollIntoView({ block: 'nearest' });
  }
  function enviar(indice, accion, delta) {
    var f = document.createElement('form');
    f.method = 'POST';
    var csrf = document.querySelector('[name=csrfmiddlewaretoken]');
    f.innerHTML = '<input type="hidden" name="csrfmiddlewaretoken" value="' + (csrf ? csrf.value : '') + '">' +
      '<input type="hidden" name="accion" value="' + accion + '">' +
      '<input type="hidden" name="indice" value="' + indice + '">' +
      (delta ? '<input type="hidden" name="delta" value="' + delta + '">' : '');
    document.body.appendChild(f);
    f.submit();
  }
  function badge() {
    var b = document.getElementById('buffer-cantidad');
    if (!b) {
      b = document.createElement('div');
      b.id = 'buffer-cantidad';
      b.style.cssText = 'position:fixed;bottom:110px;right:24px;z-index:60;background:#0f172a;color:#fff;padding:10px 18px;border-radius:10px;font-size:1.1rem;font-weight:700;box-shadow:0 4px 14px rgba(0,0,0,.4);display:none';
      document.body.appendChild(b);
    }
    return b;
  }
  function pintarBuffer() {
    var b = badge();
    if (buffer) {
      var ls = lineas();
      var nombre = (sel >= 0 && ls[sel]) ? ls[sel].querySelector('span').textContent.split('×')[0].trim() : '';
      b.textContent = nombre + ' → nueva cantidad: ' + buffer;
      b.style.display = 'block';
    } else {
      b.style.display = 'none';
    }
  }
  function teclearBuffer(k) {
    buffer += (k === ',') ? '.' : k;
    clearTimeout(bufferTimer);
    bufferTimer = setTimeout(function () { buffer = ''; pintarBuffer(); }, 3000);
    pintarBuffer();
  }
  function confirmarBuffer() {
    var ls = lineas();
    if (sel < 0 || !ls[sel] || !buffer) return;
    var nueva = parseFloat(buffer);
    buffer = '';
    pintarBuffer();
    if (isNaN(nueva) || nueva <= 0) return;
    var actual = parseFloat((ls[sel].getAttribute('data-cantidad') || '0').replace(',', '.'));
    var delta = Math.round((nueva - actual) * 1000) / 1000;
    if (delta !== 0) enviar(sel, 'cantidad', String(delta));
  }

  document.addEventListener('keydown', function (e) {
    if (!document.querySelector('.pos-fullscreen')) return;
    if (['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)) return;
    var ls = lineas();

    if (e.key === 'ArrowUp') { e.preventDefault(); navegar('up'); return; }
    if (e.key === 'ArrowDown') { e.preventDefault(); navegar('down'); return; }
    if (!ls.length || sel < 0) return;

    if (e.key === 'Delete') { e.preventDefault(); buffer = ''; pintarBuffer(); enviar(sel, 'quitar'); return; }
    if (e.key === '+' || e.key === '=' || e.code === 'NumpadAdd') { e.preventDefault(); enviar(sel, 'cantidad', '1'); return; }
    if (e.key === '-' || e.code === 'NumpadSubtract' || e.code === 'Minus') { e.preventDefault(); enviar(sel, 'cantidad', '-1'); return; }

    if (/^[0-9.,]$/.test(e.key)) { e.preventDefault(); teclearBuffer(e.key); return; }
    if (e.key === 'Backspace' && buffer) { e.preventDefault(); buffer = buffer.slice(0, -1); pintarBuffer(); return; }
    if (e.key === 'Enter' && buffer) { e.preventDefault(); confirmarBuffer(); return; }
    if (e.key === 'Escape' && buffer) { e.preventDefault(); e.stopImmediatePropagation(); buffer = ''; pintarBuffer(); return; }
  });

  document.addEventListener('DOMContentLoaded', function () {
    var sc = document.querySelector('.ticket-scroll');
    if (sc) sc.scrollTop = sc.scrollHeight;
  });
})();

// ===== POS: tabla de resultados (flechas + cantidad + Enter) =====
(function () {
  var selTabla = -1;
  function filas() {
    return Array.prototype.slice.call(
      document.querySelectorAll('.pos-left table tbody tr')
    ).filter(function (tr) { return tr.querySelector('form.fila-agregar'); });
  }
  function inputDe(fila) { return fila.querySelector('input[name="cantidad"]'); }
  function pintar() {
    filas().forEach(function (f, i) { f.classList.toggle('fila-seleccionada', i === selTabla); });
    if (selTabla >= 0 && filas()[selTabla]) filas()[selTabla].scrollIntoView({ block: 'nearest' });
  }
  document.addEventListener('focusin', function (e) {
    var tr = e.target.closest ? e.target.closest('tr') : null;
    if (tr && tr.querySelector('form.fila-agregar')) {
      var idx = filas().indexOf(tr);
      if (idx >= 0) { selTabla = idx; pintar(); }
    }
  });
  document.addEventListener('keydown', function (e) {
    if (!document.querySelector('.pos-fullscreen')) return;
    var fl = filas();
    if (!fl.length) return;
    var active = document.activeElement;
    var tag = active ? active.tagName : '';
    var enBusqueda = active === document.querySelector('input[name="q"]');
    var enInputFila = !!(active && active.closest && active.closest('form.fila-agregar') && tag === 'INPUT');
    if (tag === 'TEXTAREA' || tag === 'SELECT') return;
    if (tag === 'INPUT' && !enBusqueda && !enInputFila) return;

    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault(); e.stopImmediatePropagation();
      selTabla = e.key === 'ArrowDown'
        ? (selTabla + 1) % fl.length
        : (selTabla <= 0 ? fl.length - 1 : selTabla - 1);
      pintar();
      if (enInputFila) { var i = inputDe(fl[selTabla]); if (i) i.focus(); }
    } else if (/^[0-9.,]$/.test(e.key) && (enBusqueda || tag === '' || tag === 'BODY')) {
      e.preventDefault(); e.stopImmediatePropagation();
      if (selTabla < 0) { selTabla = 0; pintar(); }
      var inp = inputDe(fl[selTabla]);
      if (inp) { inp.focus(); inp.value = (e.key === ',') ? '.' : e.key; }
    } else if (e.key === 'Enter' && selTabla >= 0) {
      e.preventDefault(); e.stopImmediatePropagation();
      var f = fl[selTabla].querySelector('form');
      if (f) f.submit();
    } else if (e.key === 'Escape' && enInputFila) {
      e.preventDefault(); e.stopImmediatePropagation();
      var q = document.querySelector('input[name="q"]');
      if (q) q.focus();
    }
  }, true);
})();
