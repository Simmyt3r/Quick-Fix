(function () {
  document.querySelectorAll('[data-promote-toggle]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var id = btn.getAttribute('data-promote-toggle');
      var row = document.getElementById('promote-row-' + id);
      if (row) row.hidden = !row.hidden;
    });
  });
})();
