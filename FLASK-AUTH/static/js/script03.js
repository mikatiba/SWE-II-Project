document.addEventListener("DOMContentLoaded", function () {
    const services = document.querySelectorAll(".service");
    
    services.forEach(service => {
        const vincularButton = service.querySelector(".vincular");
        const desvincularButton = service.querySelector(".desvincular");
        
        vincularButton.addEventListener("click", function () {
            vincularButton.style.display = "none";
            desvincularButton.style.display = "none";
            
            const serviceName = service.querySelector("img").alt;
            const form = document.createElement("form");
            form.classList.add("vinculacion-form");
            form.innerHTML = `
                <h3>Vincular cuenta de ${serviceName}</h3>
                <div class="form-group">
                    <label for="fullName">Nombre Completo:</label>
                    <input type="text" id="fullName" name="fullName" required>
                </div>
                
                <div class="form-group">
                    <label for="accountNumber">Número de Cuenta:</label>
                    <input type="text" id="accountNumber" name="accountNumber" required>
                </div>
                
                <div class="form-group">
                    <label for="email">Correo Electrónico:</label>
                    <input type="email" id="email" name="email" required>
                </div>
                
                <div class="form-group">
                    <label for="password">Contraseña:</label>
                    <input type="password" id="password" name="password" required>
                </div>
                
                <div class="form-group">
                    <label for="address">Dirección:</label>
                    <input type="text" id="address" name="address" required>
                </div>
                
                <div class="form-buttons">
                    <button type="submit" class="submit-btn">Enviar</button>
                    <button type="button" class="cancel-btn">Cancelar</button>
                </div>
            `;
            
            service.appendChild(form);
            
            form.querySelector(".cancel-btn").addEventListener("click", function () {
                form.remove();
                vincularButton.style.display = "inline-block";
                desvincularButton.style.display = "inline-block";
            });
            
            form.addEventListener("submit", function (event) {
                event.preventDefault();
                alert(`Cuenta de ${serviceName} vinculada correctamente.`);
                form.remove();
                vincularButton.style.display = "none";
                desvincularButton.style.display = "inline-block";
            });
        });
        
        desvincularButton.addEventListener("click", function () {
            const serviceName = service.querySelector("img").alt;
            if (confirm(`¿Estás seguro de que deseas desvincular tu cuenta de ${serviceName}?`)) {
                alert(`Cuenta de ${serviceName} desvinculada correctamente.`);
                vincularButton.style.display = "inline-block";
                desvincularButton.style.display = "none";
            }
        });
    });
});
