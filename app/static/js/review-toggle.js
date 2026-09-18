(function () {
  document.querySelectorAll('[data-review-toggle]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var id = btn.getAttribute('data-review-toggle');
      var row = document.getElementById('review-row-' + id);
      if (row) row.hidden = !row.hidden;
    });
  });
})();
