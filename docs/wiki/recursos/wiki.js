/* Wiki de MantiTools: buscador, índice de la página, visor de imágenes y copiar código. Sin dependencias. */
(function () {
  "use strict";

  function normal(texto) {
    return (texto || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
  }
  function escapar(texto) {
    return texto.replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; });
  }

  // --- Buscador
  var campo = document.getElementById("buscar");
  var caja = document.getElementById("resultados");
  var paginas = window.WIKI_INDICE || [];
  var elegido = -1;

  function fragmento(texto, terminos) {
    var n = normal(texto), pos = -1;
    for (var i = 0; i < terminos.length && pos < 0; i++) pos = n.indexOf(terminos[i]);
    if (pos < 0) return "";
    var ini = Math.max(0, pos - 60), trozo = texto.substr(ini, 170);
    var html = escapar(trozo);
    terminos.forEach(function (t) {
      if (!t) return;
      var nt = normal(trozo), salida = "", ultimo = 0, k;
      while ((k = nt.indexOf(t, ultimo)) >= 0) {
        salida += escapar(trozo.slice(ultimo, k)) + "<mark>" + escapar(trozo.substr(k, t.length)) + "</mark>";
        ultimo = k + t.length;
      }
      if (ultimo) html = salida + escapar(trozo.slice(ultimo));
    });
    return (ini > 0 ? "…" : "") + html + "…";
  }

  function buscar(consulta) {
    var terminos = normal(consulta).split(/\s+/).filter(function (t) { return t.length > 1; });
    if (!terminos.length) { caja.hidden = true; return; }
    var hallados = [];
    paginas.forEach(function (p) {
      var titulo = normal(p.t), texto = normal(p.x), puntos = 0, todos = true;
      terminos.forEach(function (t) {
        var enTexto = texto.indexOf(t) >= 0, enTitulo = titulo.indexOf(t) >= 0;
        if (!enTexto && !enTitulo) todos = false;
        if (enTitulo) puntos += 10;
        if (enTexto) puntos += 1 + Math.min(5, texto.split(t).length - 1);
      });
      if (!todos) return;
      var seccion = null;
      (p.s || []).some(function (s) {
        var ns = normal(s[0]);
        if (terminos.every(function (t) { return ns.indexOf(t) >= 0; })) { seccion = s; return true; }
        return false;
      });
      if (seccion) puntos += 6;
      hallados.push({ p: p, puntos: puntos, seccion: seccion });
    });
    hallados.sort(function (a, b) { return b.puntos - a.puntos; });
    elegido = -1;
    if (!hallados.length) {
      caja.innerHTML = '<div class="vacio">Nada encontrado para «' + escapar(consulta) + "».</div>";
    } else {
      caja.innerHTML = hallados.slice(0, 12).map(function (h) {
        var destino = h.p.p + ".html" + (h.seccion ? "#" + h.seccion[1] : "");
        var titulo = escapar(h.p.t) + (h.seccion ? " › " + escapar(h.seccion[0]) : "");
        return '<a href="' + destino + '"><b>' + titulo + "</b><small>" + fragmento(h.p.x, terminos) + "</small></a>";
      }).join("");
    }
    caja.hidden = false;
  }

  if (campo) {
    campo.addEventListener("input", function () { buscar(campo.value); });
    campo.addEventListener("keydown", function (e) {
      var enlaces = caja.querySelectorAll("a");
      if (e.key === "ArrowDown" || e.key === "ArrowUp") {
        e.preventDefault();
        if (!enlaces.length) return;
        elegido = (elegido + (e.key === "ArrowDown" ? 1 : -1) + enlaces.length) % enlaces.length;
        enlaces.forEach(function (a, i) { a.classList.toggle("activo", i === elegido); });
      } else if (e.key === "Enter") {
        var a = enlaces[elegido >= 0 ? elegido : 0];
        if (a) window.location.href = a.getAttribute("href");
      } else if (e.key === "Escape") {
        caja.hidden = true; campo.blur();
      }
    });
    document.addEventListener("click", function (e) {
      if (!e.target.closest(".buscador")) caja.hidden = true;
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "/" && document.activeElement !== campo) { e.preventDefault(); campo.focus(); }
    });
  }

  // --- Menú en móvil
  var boton = document.querySelector(".menu-movil");
  if (boton) boton.addEventListener("click", function () { document.body.classList.toggle("nav-abierta"); });

  // --- Índice: resalta la sección visible
  var enlacesIndice = document.querySelectorAll(".indice a");
  if (enlacesIndice.length && "IntersectionObserver" in window) {
    var porId = {};
    enlacesIndice.forEach(function (a) { porId[a.getAttribute("href").slice(1)] = a; });
    var observador = new IntersectionObserver(function (entradas) {
      entradas.forEach(function (en) {
        if (en.isIntersecting && porId[en.target.id]) {
          enlacesIndice.forEach(function (a) { a.classList.remove("visible"); });
          porId[en.target.id].classList.add("visible");
        }
      });
    }, { rootMargin: "-70px 0px -70% 0px" });
    document.querySelectorAll("article h2[id], article h3[id]").forEach(function (h) { observador.observe(h); });
  }

  // --- Visor de imágenes
  var visor = document.getElementById("visor");
  document.querySelectorAll("a.zoom").forEach(function (a) {
    a.addEventListener("click", function (e) {
      e.preventDefault();
      visor.querySelector("img").src = a.getAttribute("href");
      visor.hidden = false;
    });
  });
  if (visor) {
    visor.addEventListener("click", function () { visor.hidden = true; });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") visor.hidden = true; });
  }

  // --- Copiar código
  document.querySelectorAll(".codigo .copiar").forEach(function (b) {
    b.addEventListener("click", function () {
      var texto = b.parentNode.querySelector("code").innerText;
      var hecho = function () { b.textContent = "Copiado"; setTimeout(function () { b.textContent = "Copiar"; }, 1400); };
      if (navigator.clipboard) navigator.clipboard.writeText(texto).then(hecho, hecho);
      else hecho();
    });
  });
})();
