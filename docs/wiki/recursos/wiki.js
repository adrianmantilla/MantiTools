// Wiki de MantiTools: buscador, menú en pantallas estrechas, índice de la página y ampliar imágenes.
// Funciona abriendo los .html directamente (file://), sin servidor ni conexión.
(function () {
  "use strict";

  // --- Menú lateral en móvil
  var boton = document.querySelector(".abrir-menu");
  if (boton) {
    boton.addEventListener("click", function () {
      var abierto = document.body.classList.toggle("menu-abierto");
      boton.setAttribute("aria-expanded", abierto ? "true" : "false");
    });
  }

  // --- Buscador
  var paginas = window.WIKI_PAGINAS || [];
  var entrada = document.getElementById("buscar");
  var lista = document.getElementById("resultados");

  function sinTildes(texto) {
    return texto.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
  }
  function escapar(texto) {
    return texto.replace(/[&<>"]/g, function (c) { return {"&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;"}[c]; });
  }
  var indice = paginas.map(function (p) {
    return {p: p, t: sinTildes(p.t), x: sinTildes(p.x), h: p.h.map(function (h) { return [h[0], h[1], sinTildes(h[1])]; })};
  });

  function fragmento(p, pos, largo) {
    var desde = Math.max(0, pos - 40);
    var trozo = p.x.slice(desde, pos + largo + 70);
    return (desde > 0 ? "…" : "") + escapar(trozo.slice(0, pos - desde)) + "<mark>" +
      escapar(trozo.slice(pos - desde, pos - desde + largo)) + "</mark>" + escapar(trozo.slice(pos - desde + largo)) + "…";
  }

  function buscar(consulta) {
    var q = sinTildes(consulta.trim());
    if (q.length < 2) { lista.hidden = true; lista.innerHTML = ""; return; }
    var palabras = q.split(/\s+/);
    var encontrados = [];
    indice.forEach(function (e) {
      var puntos = 0;
      palabras.forEach(function (w) {
        if (e.t.indexOf(w) >= 0) puntos += 10;
        e.h.forEach(function (h) { if (h[2].indexOf(w) >= 0) puntos += 4; });
        var veces = e.x.split(w).length - 1;
        puntos += Math.min(veces, 12);
      });
      if (!palabras.every(function (w) { return e.t.indexOf(w) >= 0 || e.x.indexOf(w) >= 0; })) return;
      var ancla = "";
      e.h.forEach(function (h) { if (!ancla && h[2].indexOf(palabras[0]) >= 0) ancla = h[0]; });
      encontrados.push({e: e, puntos: puntos, ancla: ancla, pos: e.x.indexOf(palabras[0])});
    });
    encontrados.sort(function (a, b) { return b.puntos - a.puntos; });
    if (!encontrados.length) {
      lista.innerHTML = '<li class="vacio">Nada con «' + escapar(consulta) + '»</li>';
    } else {
      lista.innerHTML = encontrados.slice(0, 12).map(function (r, i) {
        return '<li><a href="' + r.e.p.p + '.html' + (r.ancla ? "#" + r.ancla : "") + '"' + (i === 0 ? ' class="activo"' : "") +
          ">" + escapar(r.e.p.t) + (r.pos >= 0 ? "<small>" + fragmento(r.e.p, r.pos, palabras[0].length) + "</small>" : "") + "</a></li>";
      }).join("");
    }
    lista.hidden = false;
  }

  if (entrada && lista) {
    entrada.addEventListener("input", function () { buscar(entrada.value); });
    entrada.addEventListener("keydown", function (ev) {
      var enlaces = Array.prototype.slice.call(lista.querySelectorAll("a"));
      var actual = enlaces.findIndex(function (a) { return a.classList.contains("activo"); });
      if (ev.key === "ArrowDown" || ev.key === "ArrowUp") {
        ev.preventDefault();
        if (!enlaces.length) return;
        if (actual >= 0) enlaces[actual].classList.remove("activo");
        actual = (actual + (ev.key === "ArrowDown" ? 1 : -1) + enlaces.length) % enlaces.length;
        enlaces[actual].classList.add("activo");
        enlaces[actual].scrollIntoView({block: "nearest"});
      } else if (ev.key === "Enter" && actual >= 0) {
        window.location.href = enlaces[actual].getAttribute("href");
      } else if (ev.key === "Escape") {
        entrada.value = ""; buscar("");
      }
    });
    document.addEventListener("keydown", function (ev) {
      if (ev.key === "/" && document.activeElement !== entrada) { ev.preventDefault(); entrada.focus(); }
    });
  }

  // --- Índice de la página: resalta el apartado que se está leyendo
  var enlacesIndice = Array.prototype.slice.call(document.querySelectorAll(".indice a"));
  if (enlacesIndice.length && "IntersectionObserver" in window) {
    var porId = {};
    enlacesIndice.forEach(function (a) { porId[a.getAttribute("href").slice(1)] = a; });
    var observador = new IntersectionObserver(function (entradas) {
      entradas.forEach(function (e) {
        if (e.isIntersecting) {
          enlacesIndice.forEach(function (a) { a.classList.remove("visible"); });
          if (porId[e.target.id]) porId[e.target.id].classList.add("visible");
        }
      });
    }, {rootMargin: "0px 0px -70% 0px"});
    document.querySelectorAll("article h2[id]").forEach(function (h) { observador.observe(h); });
  }

  // --- Ampliar imágenes y GIF con un clic
  document.querySelectorAll("figure img, article p img:not(.icono)").forEach(function (img) {
    img.addEventListener("click", function () {
      var capa = document.createElement("div");
      capa.className = "zoom";
      var grande = document.createElement("img");
      grande.src = img.src;
      grande.alt = img.alt;
      capa.appendChild(grande);
      capa.addEventListener("click", function () { capa.remove(); });
      document.addEventListener("keydown", function cerrar(ev) {
        if (ev.key === "Escape") { capa.remove(); document.removeEventListener("keydown", cerrar); }
      });
      document.body.appendChild(capa);
    });
  });
})();
