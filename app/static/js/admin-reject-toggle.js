(function () {
  document.querySelectorAll('[data-reject-toggle]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var id = btn.getAttribute('data-reject-toggle');
      var row = document.getElementById('reject-row-' + id);
      if (row) row.hidden = !row.hidden;
    });
  });
})();
