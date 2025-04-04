document.addEventListener("DOMContentLoaded", function () {
    function enviarFormulario(event, endpoint, form) {
        event.preventDefault();

        let formData = new FormData(form);

        fetch(endpoint, {
            method: "POST",
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            alert(data.mensagem);
            if (data.sucesso) {
                form.reset();
            }
        })
        .catch(error => {
            console.error("Erro ao enviar formulário:", error);
            alert("Erro ao enviar. Tente novamente.");
        });
    }

    // Formulário de contato
    document.querySelector("#contato form").addEventListener("submit", function (event) {
        enviarFormulario(event, "/enviar-contato", this);
    });

    // Formulário de denúncia
    document.querySelector("#denuncias form").addEventListener("submit", function (event) {
        enviarFormulario(event, "/enviar-denuncia", this);
    });

    // Formulário de sugestões
    document.querySelector("#sugestoes form").addEventListener("submit", function (event) {
        enviarFormulario(event, "/enviar-sugestao", this);
    });
});

// Exibir o botão ao rolar para baixo
window.onscroll = function() {
    let btn = document.getElementById("btnTopo");
    if (document.body.scrollTop > 200 || document.documentElement.scrollTop > 200) {
        btn.style.display = "block";
    } else {
        btn.style.display = "none";
    }
};

// Função para rolar suavemente para o topo
function voltarAoTopo() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
}
