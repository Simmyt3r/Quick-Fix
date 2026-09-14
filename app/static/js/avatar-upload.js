(function () {
  var input = document.getElementById("avatar-input");
  var form = document.getElementById("avatar-form");
  if (!input || !form) return;
  input.addEventListener("change", function () {
    if (input.files && input.files.length > 0) {
      form.submit();
    }
  });
})();
