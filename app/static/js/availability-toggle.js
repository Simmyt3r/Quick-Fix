(function () {
  var checkbox = document.getElementById("availability-quick-checkbox");
  if (!checkbox) return;
  checkbox.addEventListener("change", function () {
    checkbox.form.submit();
  });
})();
