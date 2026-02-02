/* Prisma ERP - Scripts Personalizados
   Funções de Máscara para CPF, CNPJ e Telefone
*/

document.addEventListener("DOMContentLoaded", function () {
  // --- MÁSCARA DE TELEFONE (9 ou 8 dígitos) ---
  const phoneInputs = document.querySelectorAll(".mask-celular");
  phoneInputs.forEach((input) => {
    input.addEventListener("input", function (e) {
      let x = e.target.value
        .replace(/\D/g, "")
        .match(/(\d{0,2})(\d{0,5})(\d{0,4})/);
      e.target.value = !x[2]
        ? x[1]
        : "(" + x[1] + ") " + x[2] + (x[3] ? "-" + x[3] : "");
    });
  });

  // --- MÁSCARA DINÂMICA (CPF ou CNPJ) ---
  const docInputs = document.querySelectorAll(".mask-documento");
  docInputs.forEach((input) => {
    input.addEventListener("input", function (e) {
      let value = e.target.value.replace(/\D/g, ""); // Remove tudo que não é número

      if (value.length > 11) {
        // É CNPJ
        value = value.replace(/^(\d{2})(\d)/, "$1.$2");
        value = value.replace(/^(\d{2})\.(\d{3})(\d)/, "$1.$2.$3");
        value = value.replace(/\.(\d{3})(\d)/, ".$1/$2");
        value = value.replace(/(\d{4})(\d)/, "$1-$2");
      } else {
        // É CPF
        value = value.replace(/(\d{3})(\d)/, "$1.$2");
        value = value.replace(/(\d{3})(\d)/, "$1.$2");
        value = value.replace(/(\d{3})(\d{1,2})$/, "$1-$2");
      }

      e.target.value = value;
    });
  });
});
