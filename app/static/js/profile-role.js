(function () {
  var customerBox = document.getElementById("profile-is-customer");
  var professionalBox = document.getElementById("profile-is-professional");
  var categoryField = document.getElementById("profile-category-field");
  if (!customerBox || !professionalBox) return;

  function sync() {
    if (categoryField) {
      categoryField.style.display = professionalBox.checked ? "flex" : "none";
    }
  }

  function guardAtLeastOne(justChanged) {
    if (!customerBox.checked && !professionalBox.checked) {
      justChanged.checked = true;
    }
  }

  [customerBox, professionalBox].forEach(function (box) {
    box.addEventListener("change", function () {
      guardAtLeastOne(box);
      sync();
    });
  });

  sync();
})();
