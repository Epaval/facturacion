// Atajos de teclado estilo POS
function aviso(msg) {
  let t = document.querySelector(".toast-aviso");
  if (!t) {
    t = document.createElement("div");
    t.className = "toast-aviso";
    document.body.appendChild(t);
  }
  t.textContent = msg;
  t.style.display = "block";
  clearTimeout(t._timer);
  t._timer = setTimeout(() => { t.style.display = "none"; }, 2500);
}

const RESTRINGIDO = "Acceso restringido: solo administradores";

document.addEventListener("keydown", function (e) {
  switch (e.key) {
    case "F1": e.preventDefault(); window.location.href = RUTAS.pos; break;
    case "F2": {
      e.preventDefault();
      const inp = document.querySelector("input[name='q']");
      if (inp) inp.focus();
      else if (RUTAS.buscar_producto) window.location.href = RUTAS.buscar_producto;
      else aviso(RESTRINGIDO);
      break;
    }
    case "F3": {
      e.preventDefault();
      const inp = document.querySelector("input[name='q_cliente']");
      if (inp) inp.focus(); else window.location.href = RUTAS.buscar_cliente;
      break;
    }
    case "F4": e.preventDefault(); window.location.href = RUTAS.nuevo_cliente; break;
    case "F5": {
      e.preventDefault();
      if (RUTAS.nuevo_producto) window.location.href = RUTAS.nuevo_producto;
      else aviso(RESTRINGIDO);
      break;
    }
    case "F6": e.preventDefault(); window.location.href = RUTAS.caja; break;
    case "F8": {
      e.preventDefault();
      const f = document.querySelector("form[data-guardar]") || document.querySelector("main form");
      if (f) { f.requestSubmit ? f.requestSubmit() : f.submit(); }
      break;
    }
    case "F9": {
      e.preventDefault();
      const f = document.querySelector("form[data-confirmar]");
      if (f) { f.requestSubmit ? f.requestSubmit() : f.submit(); }
      break;
    }
    case "F10": {
      e.preventDefault();
      const f = document.querySelector("form[data-finalizar]");
      if (f) { f.requestSubmit ? f.requestSubmit() : f.submit(); }
      break;
    }
    case "Escape": {
      const tag = (document.activeElement || {}).tagName;
      if (tag !== "INPUT" && tag !== "TEXTAREA" && tag !== "SELECT") {
        if (document.querySelector(".modal-fondo")) window.location.href = RUTAS.pos;
        else history.back();
      }
      break;
    }
  }
});

// Mensajes como toast que se ocultan solos
document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll(".mensaje").forEach(function (m) {
    const ms = m.classList.contains("error") ? 6000 : 2500;
    setTimeout(function () {
      m.style.transition = "opacity .4s";
      m.style.opacity = "0";
      setTimeout(function () { m.remove(); }, 400);
    }, ms);
  });
});

// ===== Flujo de teclado en cobro (sin mouse) =====
(function () {
  const monto = document.querySelector("input[name='monto']");
  const metodo = document.querySelector("select[name='metodo']");
  const qcli = document.querySelector("input[name='q_cliente']");
  if (!monto && !qcli) return; // no es la pantalla de cobro

  window.addEventListener("load", function () {
    // Sin cliente: foco en el buscador. Con cliente: directo al método de pago.
    if (qcli && !document.querySelector(".cliente-card")) { qcli.focus(); return; }
    if (metodo) metodo.focus();
  });

  if (metodo && monto) {
    // Enter en el select pasa al monto (flechas cambian el método)
    metodo.addEventListener("keydown", function (e) {
      if (e.key === "Enter") { e.preventDefault(); monto.focus(); }
    });
    // Enter en el monto agrega el pago y el foco regresa al select
  }
})();

// Foco automático en modales (cliente F10 y pesaje)
document.addEventListener("DOMContentLoaded", function () {
  const m = document.querySelector(".modal-caja input[name='cliente_q']") ||
            document.querySelector(".modal-caja input[type='number']");
  if (m) m.focus();
});

// Esc en cobro: volver al ticket sin mouse (aunque el foco esté en select/input)
document.addEventListener("keydown", function (e) {
  if (e.key !== "Escape") return;
  if (document.querySelector(".modal-fondo")) return;
  const volver = document.querySelector("input[name='accion'][value='volver']");
  if (volver) {
    e.preventDefault();
    volver.closest("form").submit();
  }
});

// Ctrl+Z: vaciar ticket sin mouse (con confirmación)
document.addEventListener("keydown", function (e) {
  if (!(e.ctrlKey && (e.key === "z" || e.key === "Z"))) return;
  const vaciar = document.querySelector("input[name='accion'][value='vaciar']");
  if (!vaciar) return;
  e.preventDefault();
  vaciar.closest("form").submit();
});
