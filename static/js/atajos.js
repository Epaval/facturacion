// Atajos de teclado estilo POS
document.addEventListener("keydown", function (e) {
  switch (e.key) {
    case "F1": e.preventDefault(); window.location.href = RUTAS.pos; break;
    case "F2": e.preventDefault(); window.location.href = RUTAS.buscar_producto; break;
    case "F3": e.preventDefault(); window.location.href = RUTAS.buscar_cliente; break;
    case "F4": e.preventDefault(); window.location.href = RUTAS.nuevo_cliente; break;
    case "F5": e.preventDefault(); window.location.href = RUTAS.nuevo_producto; break;
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
      if (tag !== "INPUT" && tag !== "TEXTAREA" && tag !== "SELECT") history.back();
      break;
    }
  }
});
