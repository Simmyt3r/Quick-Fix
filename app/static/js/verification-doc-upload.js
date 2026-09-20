(function () {
  var input = document.getElementById("verification-doc-input");
  var form = document.getElementById("verification-doc-form");
  if (!input || !form) return;
  input.addEventListener("change", function () {
    if (input.files && input.files.length > 0) {
      form.submit();
    }
  });
})();
