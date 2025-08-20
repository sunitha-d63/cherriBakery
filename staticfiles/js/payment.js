document.addEventListener('DOMContentLoaded', function() {
  const form = document.getElementById('paymentForm');
  
  form.addEventListener('submit', function(e) {
    let isValid = true;

    const name = form.querySelector('input[name="name"]');
    if (!/^[a-zA-Z\s'-]+$/.test(name.value)) {
      isValid = false;
      name.classList.add('is-invalid');
      name.nextElementSibling.textContent = 'Name can only contain letters, spaces, apostrophes and hyphens';
    }
    
    const location = form.querySelector('input[name="location"]');
    if (!/^[a-zA-Z0-9\s\.,\-/]+$/.test(location.value)) {
      isValid = false;
      location.classList.add('is-invalid');
      location.nextElementSibling.textContent = 'Enter a valid location (letters, numbers, spaces, and basic punctuation)';
    }

    const address = form.querySelector('textarea[name="address"]');
    if (!/^[a-zA-Z0-9\s\.,\-/#&]{10,}$/.test(address.value)) {
      isValid = false;
      address.classList.add('is-invalid');
      address.nextElementSibling.textContent = 'Address must be at least 10 characters and contain only letters, numbers, and basic punctuation';
    }

    const notes = form.querySelector('input[name="notes"]');
    if (notes.value && !/^[a-zA-Z0-9\s\.,\-!?()]*$/.test(notes.value)) {
      isValid = false;
      notes.classList.add('is-invalid');
      notes.nextElementSibling.textContent = 'Notes can only contain letters, numbers, and basic punctuation';
    }
    
    if (!isValid) {
      e.preventDefault();
    }
  });
  
  form.querySelectorAll('input, textarea').forEach(input => {
    input.addEventListener('input', function() {
      if (this.classList.contains('is-invalid')) {
        this.classList.remove('is-invalid');
      }
    });
  });
});