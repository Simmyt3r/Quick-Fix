(function () {
  document.querySelectorAll('[data-disable-toggle]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var id = btn.getAttribute('data-disable-toggle');
      var row = document.getElementById('disable-row-' + id);
      if (row) row.hidden = !row.hidden;
    });
  });
})();
