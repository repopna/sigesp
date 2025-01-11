var provincias = [
    "Bengo",
    "Benguela",
    "Bié",
    "Cabinda",
    "Cuando Cubango",
    "Cuanza Norte",
    "Cuanza Sul",
    "Cunene",
    "Huambo",
    "Huíla",
    "Luanda",
    "Lunda Norte",
    "Lunda Sul",
    "Malanje",
    "Moxico",
    "Namibe",
    "Uíge",
    "Zaire"
];

var selectProvincia = document.getElementById("provincia");

provincias.forEach(function(provincias) {
    var option = document.createElement("option");
    option.text = provincias;
    option.value = provincias;
    selectProvincia.appendChild(option);
});