// ===== POS: altura dinámica + navegación de líneas con teclado =====
(function () {
  if (window.__posInit) return;
  window.__posInit = true;

  function ajustarAltura() {
    var cont = document.querySelector('.pos-fullscreen');
    if (!cont) return;
    var rect = cont.getBoundingClientRect();
    cont.style.height = (window.innerHeight - rect.top - 10) + 'px';
  }
  window.addEventListener('resize', ajustarAltura);
  document.addEventListener('DOMContentLoaded', ajustarAltura);
  ajustarAltura();

  var sel = -1;
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
  document.addEventListener('keydown', function (e) {
    if (!document.querySelector('.pos-fullscreen')) return;
    if (['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)) return;
    if (e.key === 'ArrowUp') { e.preventDefault(); navegar('up'); }
    else if (e.key === 'ArrowDown') { e.preventDefault(); navegar('down'); }
    else if (e.key === 'Delete') { e.preventDefault(); if (sel >= 0) enviar(sel, 'quitar'); }
    else if (e.key === '+' || e.key === '=') { e.preventDefault(); if (sel >= 0) enviar(sel, 'cantidad', '1'); }
    else if (e.key === '-') { e.preventDefault(); if (sel >= 0) enviar(sel, 'cantidad', '-1'); }
  });
  document.addEventListener('DOMContentLoaded', function () {
    var sc = document.querySelector('.ticket-scroll');
    if (sc) sc.scrollTop = sc.scrollHeight;
  });
})();
