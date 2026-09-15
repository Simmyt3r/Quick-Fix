(function () {
  var form = document.getElementById("register-form");
  var categoryField = document.getElementById("category-field");
  if (!form) return;

  var customerBox = form.querySelector('input[name="is_customer"]');
  var professionalBox = form.querySelector('input[name="is_professional"]');

  function sync() {
    if (categoryField && professionalBox) {
      categoryField.style.display = professionalBox.checked ? "flex" : "none";
    }
  }

  // Don't let both boxes end up unchecked — re-check the one that was just
  // unchecked if it would leave the form with no account type selected.
  function guardAtLeastOne(justChanged) {
    if (customerBox && professionalBox && !customerBox.checked && !professionalBox.checked) {
      justChanged.checked = true;
    }
  }

  [customerBox, professionalBox].forEach(function (box) {
    if (!box) return;
    box.addEventListener("change", function () {
      guardAtLeastOne(box);
      sync();
    });
  });

  sync();
})();
