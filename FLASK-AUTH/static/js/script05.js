function mostrarFormulario(metodo) {
    const formulario = document.getElementById("formulario-pago");
    const titulo = document.getElementById("titulo-formulario");
    const overlay = document.getElementById("overlay");

    if (metodo === "PayPal" || metodo === "ACH") {
        window.location.href = metodo.toLowerCase() + ".html"; // Redirige a otra página
    } else {
        formulario.classList.remove("hidden");
        overlay.classList.add("active");
        titulo.innerText = "Ingrese los datos de " + metodo;
    }
}

// Cerrar el formulario al hacer clic fuera 
document.getElementById("overlay").addEventListener("click", function () {
    document.getElementById("formulario-pago").classList.add("hidden");
    document.getElementById("overlay").classList.remove("active");
});

// Manejar el envío del formulario
document.getElementById("payment-form").addEventListener("submit", function(event) {
    event.preventDefault(); // Evita recargar la página
    
    // Obtener el div donde aparecerá el mensaje
    let mensajeConfirmacion = document.getElementById("mensaje-confirmacion");

    // Mostrar mensaje dentro del formulario
    mensajeConfirmacion.textContent = "Método de pago guardado correctamente.";
    mensajeConfirmacion.style.display = "block";

    // Ocultar el mensaje después de 3 segundos (opcional)
    setTimeout(() => {
        mensajeConfirmacion.style.display = "none";
    }, 3000);

    // Ocultar el formulario
    document.getElementById("formulario-pago").classList.add("hidden");
    document.getElementById("overlay").classList.remove("active");
});
