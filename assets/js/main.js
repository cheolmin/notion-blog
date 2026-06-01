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

  if (toggle) {
    toggle.addEventListener("click", function () {
      var next = currentTheme() === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      try {
        localStorage.setItem("theme", next);
      } catch (e) {}
    });
  }

  // Follow system changes only when the user hasn't picked a theme.
  try {
    var mq = matchMedia("(prefers-color-scheme: dark)");
    mq.addEventListener("change", function (e) {
      if (!localStorage.getItem("theme")) {
        root.setAttribute("data-theme", e.matches ? "dark" : "light");
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
})();
