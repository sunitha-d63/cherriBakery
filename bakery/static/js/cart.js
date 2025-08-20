
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.increment').forEach(btn => {
        btn.addEventListener('click', function() {
            const input = this.parentNode.querySelector('.quantity');
            input.value = parseInt(input.value) + 1;
            updateCartItem(this.dataset.itemId, input.value);
        });
    });
    
    document.querySelectorAll('.decrement').forEach(btn => {
        btn.addEventListener('click', function() {
            const input = this.parentNode.querySelector('.quantity');
            if (input.value > 1) {
                input.value = parseInt(input.value) - 1;
                updateCartItem(this.dataset.itemId, input.value);
            }
        });
    });

    document.querySelectorAll('.remove-item').forEach(btn => {
        btn.addEventListener('click', function() {
            if (confirm('Are you sure you want to remove this item?')) {
                removeCartItem(this.dataset.itemId);
            }
        });
    });
    
    function updateCartItem(itemId, quantity) {
        fetch('{% url "update_cart_item" %}', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': '{{ csrf_token }}'
            },
            body: JSON.stringify({
                item_id: itemId,
                quantity: quantity
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            }
        });
    }
    
   function removeCartItem(itemId) {
        fetch("{% url 'remove_cart_item' %}", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": "{{ csrf_token }}"
            },
            body: JSON.stringify({
                item_id: itemId
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            }
        });
    }
});



