// =========================================================================
// Toss-inspired theme behaviors: dark-mode toggle + code copy buttons.
// =========================================================================
(function () {
  "use strict";

  // ---------- Dark-mode toggle ----------
  var root = document.documentElement;
  var toggle = document.getElementById("theme-toggle");

  function currentTheme() {
    return root.getAttribute("data-theme") === "dark" ? "dark" : "light";
  }

  // ---------- giscus theme sync ----------
  function giscusTheme() {
    return currentTheme() === "dark"
      ? (window.GISCUS_THEME_DARK || "dark")
      : (window.GISCUS_THEME_LIGHT || "light");
  }
  function setGiscusTheme() {
    var frame = document.querySelector("iframe.giscus-frame");
    if (!frame) return;
    frame.contentWindow.postMessage(
      { giscus: { setConfig: { theme: giscusTheme() } } },
      "https://giscus.app"
    );
  }
  // Set initial theme on the giscus script tag before it loads.
  (function () {
    var g = document.querySelector('script[src^="https://giscus.app/client.js"]');
    if (g) g.setAttribute("data-theme", giscusTheme());
  })();

  if (toggle) {
    toggle.addEventListener("click", function () {
      var next = currentTheme() === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      try {
        localStorage.setItem("theme", next);
      } catch (e) {}
      setGiscusTheme();
    });
  }

  // Follow system changes only when the user hasn't picked a theme.
  try {
    var mq = matchMedia("(prefers-color-scheme: dark)");
    mq.addEventListener("change", function (e) {
      if (!localStorage.getItem("theme")) {
        root.setAttribute("data-theme", e.matches ? "dark" : "light");
        setGiscusTheme();
      }
    });
  } catch (e) {}

  // ---------- Code-block copy buttons ----------
  var pres = document.querySelectorAll(".post-content pre");
  pres.forEach(function (pre) {
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "code-copy";
    btn.textContent = "복사";
    btn.setAttribute("aria-label", "코드 복사");

    btn.addEventListener("click", function () {
      var code = pre.querySelector("code");
      var text = code ? code.innerText : pre.innerText;
      function done() {
        btn.textContent = "복사됨";
        setTimeout(function () {
          btn.textContent = "복사";
        }, 1500);
      }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done).catch(fallback);
      } else {
        fallback();
      }
      function fallback() {
        var ta = document.createElement("textarea");
        ta.value = text;
        ta.style.position = "fixed";
        ta.style.opacity = "0";
        document.body.appendChild(ta);
        ta.select();
        try {
          document.execCommand("copy");
          done();
        } catch (e) {}
        document.body.removeChild(ta);
      }
    });

    pre.appendChild(btn);
  });

  // ---------- Tag filter (home) ----------
  var filterBar = document.getElementById("tag-filter");
  if (filterBar) {
    var chips = filterBar.querySelectorAll(".tag-chip");
    var cards = document.querySelectorAll(".post-card");
    var emptyMsg = document.getElementById("filter-empty");

    function applyFilter(slug) {
      var shown = 0;
      cards.forEach(function (card) {
        var tags = (card.getAttribute("data-tags") || "").split(/\s+/);
        var match = slug === "*" || tags.indexOf(slug) !== -1;
        card.hidden = !match;
        if (match) shown++;
      });
      chips.forEach(function (c) {
        c.classList.toggle("is-active", c.getAttribute("data-filter") === slug);
      });
      if (emptyMsg) emptyMsg.hidden = shown !== 0;
    }

    chips.forEach(function (chip) {
      chip.addEventListener("click", function () {
        var slug = chip.getAttribute("data-filter");
        applyFilter(slug);
        if (slug === "*") {
          history.replaceState(null, "", location.pathname + location.search);
        } else {
          history.replaceState(null, "", "#" + slug);
        }
      });
    });

    // Deep-link: /#tag-slug selects that tag on load.
    var initial = decodeURIComponent((location.hash || "").replace(/^#/, ""));
    if (initial && filterBar.querySelector('[data-filter="' + initial + '"]')) {
      applyFilter(initial);
    }
  }
})();
