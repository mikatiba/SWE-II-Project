document.addEventListener("DOMContentLoaded", function () {
    const botones = document.querySelectorAll(".pay-button");
    const formulario = document.getElementById("formulario-pago");
    const overlay = document.getElementById("overlay");
    const inputMonto = document.getElementById("payment-amount");
    const inputServicio = document.getElementById("servicio");

    botones.forEach(btn => {
        btn.addEventListener("click", () => {
            const metodo = btn.getAttribute("data-metodo");
            const monto = btn.getAttribute("data-amount");

            // Mostrar el formulario
            formulario.classList.remove("hidden");
            overlay.classList.remove("hidden");
            formulario.classList.add("active");
            overlay.classList.add("active");

            inputMonto.value = monto;
            inputServicio.value = metodo;

            console.log("Formulario mostrado para:", metodo);
        });
    });

    overlay.addEventListener("click", () => {
        formulario.classList.remove("active");
        overlay.classList.remove("active");
        formulario.classList.add("hidden");
        overlay.classList.add("hidden");
    });

    // NO usar preventDefault para que se envíe al backend
    // El backend procesará el pago y redirigirá al historial
});