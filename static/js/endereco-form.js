function getAddress() {
    var postalCode = document.getElementById("id_postal_code");
    var rua = document.getElementById("id_rua");
    var state = document.getElementById("id_state");
    var city = document.getElementById("id_city");
    var district = document.getElementById("id_district");

    fetch(`https://viacep.com.br/ws/${postalCode.value}/json/`)
        .then(response => response.json())
        .then(data => {
            rua.value = "logradouro" in data ? data.logradouro : ""
            state.value = "uf" in data ? data.uf : ""
            city.value = "localidade" in data ? data.localidade : ""
            district.value = "bairro" in data ? data.bairro : ""
        })
        .catch(() => {
            rua.value = state.value = city.value = district.value = ""
        })
}

var maskPostalCode = IMask(document.getElementById('id_postal_code'), {
    mask: '00000-000'
});