document.addEventListener('DOMContentLoaded', function() {
  const form = document.getElementById('productForm');
  const pincodeInput = document.getElementById('pincodeInput');
  const weightBtns = document.querySelectorAll('.weightbtn');
  const selectedWeightInput = document.getElementById('selectedWeight');
  const quantityInput = document.getElementById('quantityInput');
  const decrementBtn = document.getElementById('decrementQty');
  const incrementBtn = document.getElementById('incrementQty');
  const pincodeError = document.getElementById('pincodeError');
  const weightError = document.getElementById('weightError');
  const buyNowBtn = document.getElementById('buyNowBtn');

  let selectedWeight = null;

  weightBtns.forEach(btn => {
    btn.addEventListener('click', function() {
      weightBtns.forEach(b => {
        b.classList.remove('active', 'btn-dark', 'text-white');
        b.classList.add('text-black');
      });
      
      this.classList.add('active', 'btn-dark', 'text-white');
      this.classList.remove('text-black');
      selectedWeight = this.dataset.weight;
      selectedWeightInput.value = selectedWeight;
      weightError.classList.add('d-none');
    });
  });

  decrementBtn.replaceWith(decrementBtn.cloneNode(true));
  incrementBtn.replaceWith(incrementBtn.cloneNode(true));
  const freshDecrement = document.getElementById('decrementQty');
  const freshIncrement = document.getElementById('incrementQty');

  freshDecrement.addEventListener('click', function() {
    let currentValue = parseInt(quantityInput.value) || 1;
    if (currentValue > 1) {
      quantityInput.value = currentValue - 1;
      animateButton(this);
    } else {
      triggerShake(this);
    }
  });

  freshIncrement.addEventListener('click', function() {
    let currentValue = parseInt(quantityInput.value) || 1;
    if (currentValue < 99) {
      quantityInput.value = currentValue + 1;
      animateButton(this);
    } else {
      triggerShake(this);
    }
  });

  quantityInput.addEventListener('change', function() {
    let value = parseInt(this.value) || 1;
    this.value = Math.max(1, Math.min(99, value));
  });
  pincodeInput.addEventListener('input', function() {
    if (/^\d{0,6}$/.test(this.value)) {
      this.classList.remove('is-invalid');
      pincodeError.classList.add('d-none');
    } else {
      this.value = this.value.slice(0, 6);
    }
  });

  form.addEventListener('submit', function(e) {
    let isValid = true;
    if (!/^\d{6}$/.test(pincodeInput.value)) {
      pincodeInput.classList.add('is-invalid');
      pincodeError.classList.remove('d-none');
      isValid = false;
    }

    if (!selectedWeight) {
      weightError.classList.remove('d-none');
      isValid = false;
    }

    if (!isValid) {
      e.preventDefault();
      const firstError = document.querySelector('.text-danger:not(.d-none)');
      if (firstError) {
        firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    } else {
      console.log('Form submitted with:', {
        pincode: pincodeInput.value,
        weight: selectedWeight,
        quantity: quantityInput.value
      });
     
    }
  });

  function animateButton(button) {
    button.classList.add('clicked');
    setTimeout(() => button.classList.remove('clicked'), 150);
  }

  function triggerShake(button) {
    button.classList.add('shake');
    setTimeout(() => button.classList.remove('shake'), 500);
  }
});


document.addEventListener('DOMContentLoaded', function() {
  document.querySelector('.add-to-cart').addEventListener('click', function() {
    const productId = this.dataset.productId;
    const csrfToken = this.dataset.csrf;
    const weight = document.getElementById('selectedWeight').value;
    const quantity = document.getElementById('quantityInput').value;
    
    if (!weight) {
      document.getElementById('weightError').classList.remove('d-none');
      return;
    }

    fetch('{% url "add_to_cart" %}', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken
      },
      body: JSON.stringify({
        product_id: productId,
        weight: weight,
        quantity: quantity
      })
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        document.getElementById('cart-count').textContent = data.cart_count;
        alert('Product added to cart!');
      }
    });
  });
});