(function () {
  var sidebar = document.getElementById("app-sidebar");
  var scrim = document.getElementById("sidebar-scrim");
  var closeBtn = document.getElementById("sidebar-close");
  if (!sidebar || !scrim) return;

  function openSidebar() {
    sidebar.classList.add("is-open");
    scrim.classList.add("is-visible");
  }
  function closeSidebar() {
    sidebar.classList.remove("is-open");
    scrim.classList.remove("is-visible");
  }

  // Any element with id="sidebar-toggle" on the current page opens the drawer.
  var toggle = document.getElementById("sidebar-toggle");
  if (toggle) {
    toggle.addEventListener("click", function () {
      var isOpen = sidebar.classList.contains("is-open");
      if (isOpen) {
        closeSidebar();
      } else {
        openSidebar();
      }
      toggle.setAttribute("aria-expanded", String(!isOpen));
    });
  }

  if (closeBtn) closeBtn.addEventListener("click", closeSidebar);
  scrim.addEventListener("click", closeSidebar);

  Array.prototype.forEach.call(sidebar.querySelectorAll("a"), function (a) {
    a.addEventListener("click", closeSidebar);
  });

  window.addEventListener("resize", function () {
    if (window.innerWidth >= 641) closeSidebar();
  });
})();
