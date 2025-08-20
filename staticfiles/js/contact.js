document.addEventListener('DOMContentLoaded', function() {
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');

            const message = document.getElementById('message');
            if (message.value.length < 10 || message.value.length > 1000) {
                message.setCustomValidity('Message must be between 10-1000 characters');
            } else {
                message.setCustomValidity('');
            }
        }, false);
    });

    document.querySelectorAll('input, textarea').forEach(input => {
        input.addEventListener('input', function() {
            if (this.checkValidity()) {
                this.classList.remove('is-invalid');
                this.classList.add('is-valid');
            } else {
                this.classList.remove('is-valid');
            }
        });
    });
});

document.addEventListener('DOMContentLoaded', function() {
    const successAlert = document.querySelector('.alert-success');
    if (successAlert) {
        document.getElementById('contactForm').reset();
    }
});