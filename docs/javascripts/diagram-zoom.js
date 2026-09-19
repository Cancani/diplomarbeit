(function () {
  "use strict";

  function openDiagram(svg, trigger) {
    var dialog = document.createElement("dialog");
    dialog.className = "diagram-dialog";
    dialog.setAttribute("aria-label", svg.getAttribute("aria-label") || "Diagramm");
    var toolbar = document.createElement("div");
    toolbar.className = "diagram-toolbar";
    var viewport = document.createElement("div");
    viewport.className = "diagram-viewport";
    var copy = svg.cloneNode(true);
    // Prefix all IDs and CSS/fragment references to avoid collisions with the original.
    var serial = "zoom-" + Date.now() + "-";
    var markup = copy.outerHTML;
    var ids = Array.from(copy.querySelectorAll("[id]"));
    if (copy.id) ids.unshift(copy);
    ids.map(function (node) { return node.id; }).sort(function (a, b) { return b.length - a.length; }).forEach(function (id) {
      var safe = id.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
      markup = markup.replace(new RegExp('id="' + safe + '"', "g"), 'id="' + serial + id + '"');
      markup = markup.replace(new RegExp("#" + safe + "(?=[\\s{).:\"']|$)", "g"), "#" + serial + id);
    });
    var holder = document.createElement("div");
    holder.innerHTML = markup;
    copy = holder.firstElementChild;
    copy.removeAttribute("width");
    copy.removeAttribute("height");
    var baseWidth = svg.viewBox.baseVal.width || 760;
    var scale = Math.min(1, Math.max(0.3, (window.innerWidth - 80) / baseWidth));
    function draw() { copy.style.width = Math.round(baseWidth * scale) + "px"; }
    function button(label, action) {
      var element = document.createElement("button");
      element.type = "button";
      element.textContent = label;
      element.addEventListener("click", action);
      toolbar.appendChild(element);
      return element;
    }
    button("Verkleinern", function () { scale = Math.max(0.25, scale / 1.25); draw(); });
    button("Vergrössern", function () { scale = Math.min(4, scale * 1.25); draw(); });
    var close = button("Schliessen", function () { dialog.close(); });
    viewport.appendChild(copy);
    dialog.appendChild(toolbar);
    dialog.appendChild(viewport);
    dialog.addEventListener("close", function () {
      dialog.remove();
      if (trigger.isConnected) trigger.focus();
    });
    // Native modal dialogs handle Escape, focus containment and inert page content.
    document.body.appendChild(dialog);
    draw();
    dialog.showModal();
    close.focus();
  }

  function enhance() {
    document.querySelectorAll(".md-content svg.dia-svg").forEach(function (svg) {
      if (svg.dataset.zoomReady === "1") return;
      svg.dataset.zoomReady = "1";
      var wrapper = document.createElement("div");
      wrapper.className = "dia-host";
      svg.parentNode.insertBefore(wrapper, svg);
      wrapper.appendChild(svg);
      var trigger = document.createElement("button");
      trigger.type = "button";
      trigger.className = "dia-oeffnen";
      trigger.textContent = "Vergrössern";
      trigger.setAttribute("aria-label", "Diagramm vergrössern: " + (svg.getAttribute("aria-label") || "Grafik"));
      trigger.addEventListener("click", function () { openDiagram(svg, trigger); });
      wrapper.appendChild(trigger);
    });
  }
  if (typeof document$ !== "undefined" && document$.subscribe) {
    document$.subscribe(enhance);
  } else if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", enhance);
  } else {
    enhance();
  }
})();
