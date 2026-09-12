(function () {
  var form = document.getElementById("register-form");
  var categoryField = document.getElementById("category-field");
  if (!form || !categoryField) return;

  function sync() {
    var checked = form.querySelector('input[name="role"]:checked');
    categoryField.style.display = (checked && checked.value === "professional") ? "flex" : "none";
  }

  Array.prototype.forEach.call(form.querySelectorAll('input[name="role"]'), function (el) {
    el.addEventListener("change", sync);
  });
  sync();
})();
