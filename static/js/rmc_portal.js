// static/js/rmc_portal.js - RMC Client Portal JavaScript

// Tab switching
function switchTab(tabName) {
    document.querySelectorAll('.rmc-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.rmc-tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    document.getElementById(`${tabName}-tab`).classList.add('active');
    
    // Load data for the tab
    if (tabName === 'orders') loadOrders();
    if (tabName === 'account') loadAccount();
    if (tabName === 'invoices') loadInvoices();
    if (tabName === 'payments') loadPayments();
}

// Initialize tabs
document.querySelectorAll('.rmc-tab').forEach(tab => {
    tab.addEventListener('click', () => {
        switchTab(tab.dataset.tab);
    });
});

// Load concrete grades
async function loadGrades() {
    try {
        const response = await fetch('/api/rmc/grades');
        const grades = await response.json();
        
        // Populate grade selects
        document.querySelectorAll('.item-grade').forEach(select => {
            select.innerHTML = '<option value="">Select grade...</option>';
            grades.forEach(grade => {
                select.innerHTML += `<option value="${grade.id}" data-price="${grade.price_per_cubic_meter}">${grade.grade_code} - ${grade.grade_name} (₹${grade.price_per_cubic_meter}/m³)</option>`;
            });
        });
    } catch (error) {
        console.error('Error loading grades:', error);
    }
}

// Load clients (no longer needed for customer portal)
async function loadClients() {
    // This function is deprecated - customers now enter their own name
}

// Load orders
async function loadOrders() {
    const container = document.getElementById('orders-list');
    container.innerHTML = '<div class="loading-spinner"></div>';
    
    try {
        const response = await fetch('/api/rmc/orders');
        const orders = await response.json();
        
        // Load invoices
        const invoicesResponse = await fetch('/api/rmc/invoices');
        const invoices = await invoicesResponse.json();
        
        if (orders.length === 0) {
            container.innerHTML = '<p style="color: var(--text-gray); text-align: center; padding: 40px;">No orders found. Place your first order!</p>';
            return;
        }
        
        container.innerHTML = orders.map(order => {
            // Find invoice for this order
            const invoice = invoices.find(inv => inv.order_id === order.id);
            
            return `
            <div class="rmc-list-item">
                <div class="item-main">
                    <div class="item-title">${order.order_number}</div>
                    <div class="item-subtitle">Order Date: ${new Date(order.order_date).toLocaleDateString()}</div>
                    <div class="item-meta">
                        <span>Total: <strong>₹${order.total_amount?.toLocaleString() || '0'}</strong></span>
                        <span>Delivery: ${order.delivery_date || 'TBD'}</span>
                    </div>
                </div>
                <div class="item-actions">
                    <span class="item-status status-${order.status?.toLowerCase().replace(' ', '-')}">${order.status}</span>
                    ${invoice && order.status === 'Approved' ? `
                        <button class="btn-gold" onclick="downloadInvoice('${invoice.id}', '${invoice.invoice_number}')" style="margin-left: 10px;">
                            Download Invoice
                        </button>
                    ` : ''}
                </div>
            </div>
        `;
        }).join('');
    } catch (error) {
        container.innerHTML = '<p style="color: var(--danger); text-align: center;">Error loading orders.</p>';
    }
}

// Download invoice PDF
function downloadInvoice(invoiceId, invoiceNumber) {
    fetch(`/api/rmc/invoices/${invoiceId}/pdf`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.blob();
        })
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = `invoice_${invoiceNumber}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            showToast('Invoice downloaded successfully!', 'success');
        })
        .catch(error => {
            showToast('Error downloading invoice. Please try again.', 'error');
        });
}

// Load account details
async function loadAccount() {
    const container = document.getElementById('account-details');
    container.innerHTML = '<div class="loading-spinner"></div>';
    
    try {
        const response = await fetch('/api/rmc/clients');
        const clients = await response.json();
        
        if (clients.length === 0) {
            container.innerHTML = '<p style="color: var(--text-gray); text-align: center; padding: 40px;">No account found.</p>';
            return;
        }
        
        const client = clients[0];
        container.innerHTML = `
            <div class="rmc-list-item">
                <div class="item-main">
                    <div class="item-title">${client.company_name}</div>
                    <div class="item-subtitle">Contact: ${client.contact_person}</div>
                    <div class="item-meta">
                        <span>Email: <strong>${client.email}</strong></span>
                        <span>Phone: <strong>${client.phone}</strong></span>
                    </div>
                    <div class="item-meta">
                        <span>Credit Limit: <strong>₹${client.credit_limit?.toLocaleString() || '0'}</strong></span>
                        <span>Current Balance: <strong>₹${client.current_balance?.toLocaleString() || '0'}</strong></span>
                    </div>
                </div>
            </div>
        `;
    } catch (error) {
        console.error('Error loading account:', error);
        container.innerHTML = '<p style="color: var(--danger); text-align: center;">Error loading account details.</p>';
    }
}

// Load invoices
async function loadInvoices() {
    const container = document.getElementById('invoices-list');
    container.innerHTML = '<div class="loading-spinner"></div>';
    
    try {
        const response = await fetch('/api/rmc/invoices');
        const invoices = await response.json();
        
        if (invoices.length === 0) {
            container.innerHTML = '<p style="color: var(--text-gray); text-align: center; padding: 40px;">No invoices found.</p>';
            return;
        }
        
        container.innerHTML = invoices.map(invoice => `
            <div class="rmc-list-item">
                <div class="item-main">
                    <div class="item-title">${invoice.invoice_number}</div>
                    <div class="item-subtitle">Invoice Date: ${invoice.invoice_date}</div>
                    <div class="item-meta">
                        <span>Due Date: <strong>${invoice.due_date}</strong></span>
                        <span>Total: <strong>₹${invoice.total_amount?.toLocaleString() || '0'}</strong></span>
                    </div>
                </div>
                <div class="item-actions">
                    <span class="item-status status-${invoice.status?.toLowerCase()}">${invoice.status}</span>
                    <button class="btn-outline" onclick="downloadInvoicePDF('${invoice.id}')">PDF</button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading invoices:', error);
        container.innerHTML = '<p style="color: var(--danger); text-align: center;">Error loading invoices.</p>';
    }
}

// Load payments
async function loadPayments() {
    const container = document.getElementById('payments-list');
    container.innerHTML = '<div class="loading-spinner"></div>';
    
    try {
        const response = await fetch('/api/rmc/payments');
        const payments = await response.json();
        
        if (payments.length === 0) {
            container.innerHTML = '<p style="color: var(--text-gray); text-align: center; padding: 40px;">No payment records found.</p>';
            return;
        }
        
        container.innerHTML = payments.map(payment => `
            <div class="rmc-list-item">
                <div class="item-main">
                    <div class="item-title">${payment.payment_number}</div>
                    <div class="item-subtitle">Payment Date: ${payment.payment_date}</div>
                    <div class="item-meta">
                        <span>Method: <strong>${payment.payment_method}</strong></span>
                        <span>Amount: <strong>₹${payment.amount?.toLocaleString() || '0'}</strong></span>
                    </div>
                </div>
                <div class="item-actions">
                    <button class="btn-outline" onclick="downloadPaymentReceipt('${payment.id}')">Receipt</button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading payments:', error);
        container.innerHTML = '<p style="color: var(--danger); text-align: center;">Error loading payments.</p>';
    }
}

// Add order item
function addOrderItem() {
    const container = document.getElementById('order-items-container');
    const newRow = document.createElement('div');
    newRow.className = 'order-item-row';
    newRow.innerHTML = `
        <select class="item-grade" required onchange="calculateOrderTotal()">
            <option value="">Select grade...</option>
        </select>
        <input type="number" class="item-quantity" placeholder="Quantity (m³)" min="1" step="0.5" required onchange="calculateOrderTotal()">
        <input type="text" class="item-subtotal" placeholder="Subtotal" readonly>
        <button type="button" class="btn-remove-item" onclick="removeOrderItem(this)">×</button>
    `;
    container.appendChild(newRow);
    
    // Populate grades for new row
    loadGradesForRow(newRow.querySelector('.item-grade'));
}

// Remove order item
function removeOrderItem(button) {
    const container = document.getElementById('order-items-container');
    if (container.children.length > 1) {
        button.parentElement.remove();
        calculateOrderTotal();
    }
}

// Load grades for specific row
async function loadGradesForRow(select) {
    try {
        const response = await fetch('/api/rmc/grades');
        const grades = await response.json();
        
        select.innerHTML = '<option value="">Select grade...</option>';
        grades.forEach(grade => {
            select.innerHTML += `<option value="${grade.id}" data-price="${grade.price_per_cubic_meter}">${grade.grade_code} - ${grade.grade_name} (₹${grade.price_per_cubic_meter}/m³)</option>`;
        });
    } catch (error) {
        console.error('Error loading grades:', error);
    }
}

// Calculate order total
function calculateOrderTotal() {
    let total = 0;
    document.querySelectorAll('.order-item-row').forEach(row => {
        const gradeSelect = row.querySelector('.item-grade');
        const quantityInput = row.querySelector('.item-quantity');
        const subtotalInput = row.querySelector('.item-subtotal');
        
        if (gradeSelect.value && quantityInput.value) {
            const price = parseFloat(gradeSelect.selectedOptions[0].dataset.price) || 0;
            const quantity = parseFloat(quantityInput.value) || 0;
            const subtotal = price * quantity;
            subtotalInput.value = `₹${subtotal.toLocaleString()}`;
            total += subtotal;
        }
    });
    
    document.getElementById('order-total').textContent = `₹${total.toLocaleString()}`;
    return total;
}

// Submit new order
document.getElementById('new-order-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const items = [];
    document.querySelectorAll('.order-item-row').forEach(row => {
        const gradeSelect = row.querySelector('.item-grade');
        const quantityInput = row.querySelector('.item-quantity');
        
        if (gradeSelect.value && quantityInput.value) {
            const price = parseFloat(gradeSelect.selectedOptions[0].dataset.price) || 0;
            const quantity = parseFloat(quantityInput.value) || 0;
            items.push({
                grade_id: gradeSelect.value,
                quantity: quantity,
                unit_price: price,
                subtotal: price * quantity
            });
        }
    });
    
    if (items.length === 0) {
        showToast('Please add at least one item', 'error');
        return;
    }
    
    const orderData = {
        customer_name: document.getElementById('order-customer-name').value,
        phone: document.getElementById('order-phone').value,
        delivery_date: document.getElementById('order-delivery-date').value,
        delivery_address: document.getElementById('order-delivery-address').value,
        items: items,
        notes: document.getElementById('order-notes').value
    };
    
    try {
        const response = await fetch('/api/rmc/orders', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(orderData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast(`Order ${result.order_number} placed successfully!`, 'success');
            document.getElementById('new-order-form').reset();
            document.getElementById('order-items-container').innerHTML = `
                <div class="order-item-row">
                    <select class="item-grade" required onchange="calculateOrderTotal()">
                        <option value="">Select grade...</option>
                    </select>
                    <input type="number" class="item-quantity" placeholder="Quantity (m³)" min="1" step="0.5" required onchange="calculateOrderTotal()">
                    <input type="text" class="item-subtotal" placeholder="Subtotal" readonly>
                    <button type="button" class="btn-remove-item" onclick="removeOrderItem(this)">×</button>
                </div>
            `;
            loadGrades();
            calculateOrderTotal();
            switchTab('orders');
        } else {
            showToast(result.error || 'Failed to place order', 'error');
        }
    } catch (error) {
        console.error('Error submitting order:', error);
        showToast('Error submitting order', 'error');
    }
});

// Download invoice PDF
function downloadInvoicePDF(invoiceId) {
    window.open(`/api/rmc/invoice/${invoiceId}/pdf`, '_blank');
}

// Download payment receipt
function downloadPaymentReceipt(paymentId) {
    window.open(`/api/rmc/payment/${paymentId}/receipt`, '_blank');
}

// Export functions
function exportInvoices() {
    window.open('/api/rmc/export/invoices', '_blank');
}

function exportPayments() {
    window.open('/api/rmc/export/payments', '_blank');
}

// Toast notification
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = 'toast-notification';
    
    if (type === 'success') toast.style.background = 'var(--success)';
    else if (type === 'error') toast.style.background = 'var(--danger)';
    else toast.style.background = 'var(--info)';
    
    toast.classList.remove('hidden');
    
    setTimeout(() => {
        toast.classList.add('hidden');
    }, 3000);
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadUserInfo();
    loadGrades();
    loadOrders();
});

// Load user info
async function loadUserInfo() {
    try {
        const response = await fetch('/api/auth/me');
        if (response.ok) {
            const data = await response.json();
            document.getElementById('user-name').textContent = data.user.full_name;
        } else {
            // Not authenticated, redirect to login
            window.location.href = '/login';
        }
    } catch (error) {
        console.error('Error loading user info:', error);
        window.location.href = '/login';
    }
}
