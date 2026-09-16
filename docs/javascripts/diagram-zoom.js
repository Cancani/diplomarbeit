(function () {
  "use strict";
 
  var MIN = 0.2;
  var MAX = 12;
 
  function oeffne(svg) {
    var overlay = document.createElement("div");
    overlay.className = "dia-overlay";
    overlay.setAttribute("role", "dialog");
    overlay.setAttribute("aria-modal", "true");
    overlay.setAttribute("aria-label", "Diagramm in Vollbildansicht");
 
    var buehne = document.createElement("div");
    buehne.className = "dia-buehne";
 
    var kopie = svg.cloneNode(true);
    kopie.removeAttribute("width");
    kopie.removeAttribute("height");
    kopie.removeAttribute("id");
    kopie.style.maxWidth = "none";
    kopie.style.width = "1200px";
    kopie.style.height = "auto";
    buehne.appendChild(kopie);
 
    var leiste = document.createElement("div");
    leiste.className = "dia-leiste";
    leiste.innerHTML =
      '<button type="button" data-tat="raus" title="Verkleinern" aria-label="Verkleinern">&minus;</button>' +
      '<span class="dia-wert">100 %</span>' +
      '<button type="button" data-tat="rein" title="Vergrössern" aria-label="Vergrössern">&plus;</button>' +
      '<button type="button" data-tat="reset" title="Zurücksetzen" aria-label="Zurücksetzen">Zurücksetzen</button>' +
      '<button type="button" data-tat="zu" title="Schliessen" aria-label="Schliessen">Schliessen</button>';
 
    var hinweis = document.createElement("div");
    hinweis.className = "dia-hinweis";
    hinweis.textContent = "Mausrad zum Zoomen, ziehen zum Verschieben, Escape zum Schliessen";
 
    overlay.appendChild(leiste);
    overlay.appendChild(buehne);
    overlay.appendChild(hinweis);
    document.body.appendChild(overlay);
    document.body.classList.add("dia-offen");
 
    var skala = 1;
    var vx = 0;
    var vy = 0;
    var zieht = false;
    var bewegt = false;
    var startX = 0;
    var startY = 0;
    var wert = leiste.querySelector(".dia-wert");
 
    function male() {
      buehne.style.transform =
        "translate(" + vx + "px," + vy + "px) scale(" + skala + ")";
      wert.textContent = Math.round(skala * 100) + " %";
    }
 
    function zoome(faktor, px, py) {
      var neu = Math.min(MAX, Math.max(MIN, skala * faktor));
      if (neu === skala) return;
      if (px !== undefined) {
        var r = overlay.getBoundingClientRect();
        var mx = px - r.left - r.width / 2;
        var my = py - r.top - r.height / 2;
        vx = mx - (mx - vx) * (neu / skala);
        vy = my - (my - vy) * (neu / skala);
      }
      skala = neu;
      male();
    }
 
    function schliesse() {
      document.removeEventListener("keydown", aufTaste);
      document.body.classList.remove("dia-offen");
      overlay.remove();
    }
 
    function aufTaste(e) {
      if (e.key === "Escape") schliesse();
      else if (e.key === "+" || e.key === "=") zoome(1.25);
      else if (e.key === "-") zoome(0.8);
      else if (e.key === "0") { skala = 1; vx = 0; vy = 0; male(); }
    }
 
    overlay.addEventListener("wheel", function (e) {
      e.preventDefault();
      zoome(e.deltaY < 0 ? 1.15 : 1 / 1.15, e.clientX, e.clientY);
    }, { passive: false });
 
    overlay.addEventListener("pointerdown", function (e) {
      if (e.target.closest(".dia-leiste")) return;
      zieht = true;
      bewegt = false;
      startX = e.clientX - vx;
      startY = e.clientY - vy;
      overlay.setPointerCapture(e.pointerId);
      overlay.classList.add("dia-zieht");
    });
 
    overlay.addEventListener("pointermove", function (e) {
      if (!zieht) return;
      var nx = e.clientX - startX;
      var ny = e.clientY - startY;
      if (Math.abs(nx - vx) > 3 || Math.abs(ny - vy) > 3) bewegt = true;
      vx = nx;
      vy = ny;
      male();
    });
 
    overlay.addEventListener("pointerup", function () {
      if (!zieht) return;
      zieht = false;
      overlay.classList.remove("dia-zieht");
    });
 
        overlay.addEventListener("click", function (e) {
      if (bewegt) { bewegt = false; return; }
      if (e.target === overlay) schliesse();
    });
 
    leiste.addEventListener("click", function (e) {
      var b = e.target.closest("button");
      if (!b) return;
      var tat = b.getAttribute("data-tat");
      if (tat === "rein") zoome(1.25);
      else if (tat === "raus") zoome(0.8);
      else if (tat === "reset") { skala = 1; vx = 0; vy = 0; male(); }
      else if (tat === "zu") schliesse();
    });
 
    document.addEventListener("keydown", aufTaste);
    male();
  }
 
    function findeDiagramme() {
    var wahl = [
      ".mermaid svg",
      "pre.mermaid svg",
      '[class*="mermaid"] svg',
      'svg[id*="mermaid" i]',
      "svg[aria-roledescription]"
    ].join(",");
    var liste = [];
    document.querySelectorAll(wahl).forEach(function (svg) {
      if (svg.closest(".dia-overlay")) return;
      if (liste.indexOf(svg) === -1) liste.push(svg);
    });
    return liste;
  }
 
  function ruesteAus() {
    var gefunden = 0;
    findeDiagramme().forEach(function (svg) {
      var host = svg.parentElement;
      if (!host) return;
      gefunden++;
      if (host.dataset.zoomBereit === "1") return;
      host.dataset.zoomBereit = "1";
      host.classList.add("dia-host");
 
      var knopf = document.createElement("button");
      knopf.type = "button";
      knopf.className = "dia-oeffnen";
      knopf.title = "Diagramm vergrössern";
      knopf.setAttribute("aria-label", "Diagramm vergrössern");
      knopf.textContent = "Vergrössern";
      knopf.addEventListener("click", function (e) {
        e.preventDefault();
        oeffne(svg);
      });
      host.appendChild(knopf);
 
      host.addEventListener("dblclick", function () { oeffne(svg); });
    });
    return gefunden;
  }
 
  function start() {
    var versuche = 0;
    var timer = setInterval(function () {
      ruesteAus();
      if (++versuche > 60) clearInterval(timer);
    }, 250);
  }
 
  if (typeof document$ !== "undefined" && document$.subscribe) {
    document$.subscribe(start);
  } else if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();