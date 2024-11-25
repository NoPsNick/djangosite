document.addEventListener('DOMContentLoaded', function() {
    var input = document.querySelector("#id_number");

    var iti = intlTelInput(input, {
        initialCountry: "br",
        utilsScript: "/static/js/intl-tel-input/build/js/utils.js",
        autoPlaceholder: "aggressive",
        nationalMode: false,
        separateDialCode: true,
    });

    input.addEventListener('blur', function() {
        var isValid = iti.isValidNumber();

        if (isValid) {
            input.value = iti.getNumber();
        } else {
            input.value = '';
        }
    });
});