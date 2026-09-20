(function () {
  var customerBox = document.getElementById("profile-is-customer");
  var professionalBox = document.getElementById("profile-is-professional");
  var toggledFields = [
    document.getElementById("profile-category-field"),
    document.getElementById("profile-coverage-field"),
    document.getElementById("profile-available-field"),
  ];
  if (!customerBox || !professionalBox) return;

  function sync() {
    toggledFields.forEach(function (field) {
      if (!field) return;
      field.style.display = professionalBox.checked ? "" : "none";
    });
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
