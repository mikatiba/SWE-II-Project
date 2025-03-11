document.addEventListener("DOMContentLoaded", () => {
    document.querySelector('form').addEventListener('submit', function(e){
        const pwd = document.getElementById('password').value;
        const confirmPwd = document.getElementById('confirm_password').value;

        if (pwd !== confirmPwd) {
            e.preventDefault();
            alert('Passwords do not match!');
        }
    });
});