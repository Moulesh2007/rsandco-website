// static/js/rmc_admin.js - RMC Admin Dashboard JavaScript

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
    if (tabName === 'dashboard') loadDashboard();
    if (tabName === 'orders') loadAllOrders();
    if (tabName === 'clients') loadClients();
    if (tabName === 'invoices') loadInvoices();
}

// Initialize tabs
document.querySelectorAll('.rmc-tab').forEach(tab => {
    tab.addEventListener('click', () => {
        switchTab(tab.dataset.tab);
    });
});

// Load dashboard stats and recent data
async function loadDashboard() {
    try {
        // Load orders for stats
        const ordersResponse = await fetch('/api/rmc/orders');
        const orders = await ordersResponse.json();
        
        // Load clients
        const clientsResponse = await fetch('/api/rmc/clients');
        const clients = await clientsResponse.json();
        
        // Load invoices
        const invoicesResponse = await fetch('/api/rmc/invoices');
        const invoices = await invoicesResponse.json();
        
        // Update stats
        document.getElementById('stat-orders').textContent = orders.length;
        document.getElementById('stat-clients').textContent = clients.length;
        document.getElementById('stat-invoices').textContent = invoices.filter(i => i.status === 'Sent').length;
        
        const totalRevenue = orders.reduce((sum, order) => sum + (order.total_amount || 0), 0);
        document.getElementById('stat-revenue').textContent = `₹${totalRevenue.toLocaleString()}`;
        
        // Load recent orders
        loadRecentOrders(orders);
        
        // Load pending approvals
        loadPendingOrders(orders);
        
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

// Load recent orders
function loadRecentOrders(orders) {
    const container = document.getElementById('recent-orders-list');
    const recentOrders = orders.slice(-5).reverse();
    
    if (recentOrders.length === 0) {
        container.innerHTML = '<p style="color: var(--text-gray); text-align: center; padding: 20px;">No recent orders.</p>';
        return;
    }
    
    container.innerHTML = recentOrders.map(order => `
        <div class="rmc-list-item" onclick="showOrderDetail('${order.id}')">
            <div class="item-main">
                <div class="item-title">${order.order_number}</div>
                <div class="item-subtitle">${new Date(order.order_date).toLocaleDateString()}</div>
                <div class="item-meta">
                    <span>Customer: <strong>${order.customer_name || order.client_id || 'N/A'}</strong></span>
                    <span>Total: <strong>₹${order.total_amount?.toLocaleString() || '0'}</strong></span>
                </div>
            </div>
            <div class="item-actions">
                <span class="item-status status-${order.status?.toLowerCase().replace(' ', '-')}">${order.status}</span>
            </div>
        </div>
    `).join('');
}

// Load pending orders
function loadPendingOrders(orders) {
    const container = document.getElementById('pending-orders-list');
    const pendingOrders = orders.filter(o => o.status === 'Pending');
    
    if (pendingOrders.length === 0) {
        container.innerHTML = '<p style="color: var(--text-gray); text-align: center; padding: 20px;">No pending approvals.</p>';
        return;
    }
    
    container.innerHTML = pendingOrders.map(order => `
        <div class="rmc-list-item">
            <div class="item-main">
                <div class="item-title">${order.order_number}</div>
                <div class="item-subtitle">${new Date(order.order_date).toLocaleDateString()}</div>
                <div class="item-meta">
                    <span>Customer: <strong>${order.customer_name || order.client_id || 'N/A'}</strong></span>
                    <span>Total: <strong>₹${order.total_amount?.toLocaleString() || '0'}</strong></span>
                </div>
            </div>
            <div class="item-actions">
                <button class="btn-gold" onclick="approveOrder('${order.id}')">Approve</button>
            </div>
        </div>
    `).join('');
}

// Load all orders
async function loadAllOrders() {
    const container = document.getElementById('all-orders-list');
    const statusFilter = document.getElementById('order-status-filter').value;
    container.innerHTML = '<div class="loading-spinner"></div>';
    
    try {
        let url = '/api/rmc/orders';
        if (statusFilter) {
            // For mock mode, we'll filter client-side
        }
        
        const response = await fetch(url);
        let orders = await response.json();
        
        // Filter by status if specified
        if (statusFilter) {
            orders = orders.filter(o => o.status === statusFilter);
        }
        
        if (orders.length === 0) {
            container.innerHTML = '<p style="color: var(--text-gray); text-align: center; padding: 40px;">No orders found.</p>';
            return;
        }
        
        container.innerHTML = orders.map(order => `
            <div class="rmc-list-item" onclick="showOrderDetail('${order.id}')">
                <div class="item-main">
                    <div class="item-title">${order.order_number}</div>
                    <div class="item-subtitle">${new Date(order.order_date).toLocaleDateString()}</div>
                    <div class="item-meta">
                        <span>Customer: <strong>${order.customer_name || order.client_id || 'N/A'}</strong></span>
                        <span>Total: <strong>₹${order.total_amount?.toLocaleString() || '0'}</strong></span>
                        <span>Delivery: <strong>${order.delivery_date || 'TBD'}</strong></span>
                    </div>
                </div>
                <div class="item-actions">
                    <span class="item-status status-${order.status?.toLowerCase().replace(' ', '-')}">${order.status}</span>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading orders:', error);
        container.innerHTML = '<p style="color: var(--danger); text-align: center;">Error loading orders.</p>';
    }
}

// Status filter change
document.getElementById('order-status-filter')?.addEventListener('change', loadAllOrders);

// Load clients
async function loadClients() {
    const container = document.getElementById('clients-list');
    container.innerHTML = '<div class="loading-spinner"></div>';
    
    try {
        const response = await fetch('/api/rmc/clients');
        const clients = await response.json();
        
        if (clients.length === 0) {
            container.innerHTML = '<p style="color: var(--text-gray); text-align: center; padding: 40px;">No clients found.</p>';
            return;
        }
        
        container.innerHTML = clients.map(client => `
            <div class="rmc-list-item">
                <div class="item-main">
                    <div class="item-title">${client.company_name}</div>
                    <div class="item-subtitle">${client.contact_person}</div>
                    <div class="item-meta">
                        <span>Email: <strong>${client.email}</strong></span>
                        <span>Phone: <strong>${client.phone}</strong></span>
                    </div>
                    <div class="item-meta">
                        <span>Credit Limit: <strong>₹${client.credit_limit?.toLocaleString() || '0'}</strong></span>
                        <span>Balance: <strong>₹${client.current_balance?.toLocaleString() || '0'}</strong></span>
                    </div>
                </div>
                <div class="item-actions">
                    <span class="item-status status-approved">${client.is_active ? 'Active' : 'Inactive'}</span>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading clients:', error);
        container.innerHTML = '<p style="color: var(--danger); text-align: center;">Error loading clients.</p>';
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
                        <span>Order ID: <strong>${invoice.order_id}</strong></span>
                        <span>Total: <strong>₹${invoice.total_amount?.toLocaleString() || '0'}</strong></span>
                        <span>Due: <strong>${invoice.due_date}</strong></span>
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

// Approve order
async function approveOrder(orderId) {
    if (!confirm('Are you sure you want to approve this order? An invoice will be automatically generated.')) return;
    
    try {
        const response = await fetch(`/api/rmc/orders/${orderId}/approve`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ approved_by: 'Admin' })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast(`Order approved! Invoice ${result.invoice_number} generated.`, 'success');
            loadDashboard();
        } else {
            showToast(result.error || 'Failed to approve order', 'error');
        }
    } catch (error) {
        console.error('Error approving order:', error);
        showToast('Error approving order', 'error');
    }
}

// Show order detail
async function showOrderDetail(orderId) {
    try {
        const response = await fetch('/api/rmc/orders');
        const orders = await response.json();
        const order = orders.find(o => o.id === orderId);
        
        if (!order) {
            showToast('Order not found', 'error');
            return;
        }
        
        const content = document.getElementById('order-detail-content');
        content.innerHTML = `
            <div class="detail-section">
                <h4>Order Information</h4>
                <div class="detail-row"><span>Order Number:</span><span>${order.order_number}</span></div>
                <div class="detail-row"><span>Order Date:</span><span>${new Date(order.order_date).toLocaleDateString()}</span></div>
                <div class="detail-row"><span>Customer Name:</span><span>${order.customer_name || order.client_id || 'N/A'}</span></div>
                <div class="detail-row"><span>Phone:</span><span>${order.phone || 'N/A'}</span></div>
                <div class="detail-row"><span>Delivery Date:</span><span>${order.delivery_date || 'TBD'}</span></div>
                <div class="detail-row"><span>Delivery Address:</span><span>${order.delivery_address || 'N/A'}</span></div>
                <div class="detail-row"><span>Status:</span><span>${order.status}</span></div>
                <div class="detail-row"><span>Total Amount:</span><span>₹${order.total_amount?.toLocaleString() || '0'}</span></div>
                <div class="detail-row"><span>Notes:</span><span>${order.notes || 'N/A'}</span></div>
            </div>
            
            <div class="detail-section">
                <h4>Order Items</h4>
                ${order.items ? `
                    <table class="order-items-table">
                        <thead>
                            <tr>
                                <th>Grade ID</th>
                                <th>Quantity (m³)</th>
                                <th>Unit Price</th>
                                <th>Subtotal</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${order.items.map(item => `
                                <tr>
                                    <td>${item.grade_id}</td>
                                    <td>${item.quantity}</td>
                                    <td>₹${item.unit_price?.toLocaleString() || '0'}</td>
                                    <td>₹${item.subtotal?.toLocaleString() || '0'}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                ` : '<p>No items found</p>'}
            </div>
            
            <div class="order-actions">
                ${order.status === 'Pending' ? `<button class="btn-gold" onclick="approveOrder('${order.id}'); closeModal('order-detail-modal');">Approve Order</button>` : ''}
                <select onchange="updateOrderStatus('${order.id}', this.value)" class="filter-select">
                    <option value="">Update Status...</option>
                    <option value="Approved">Approved</option>
                    <option value="In Production">In Production</option>
                    <option value="Dispatched">Dispatched</option>
                    <option value="Delivered">Delivered</option>
                    <option value="Cancelled">Cancelled</option>
                    <option value="On Hold">On Hold</option>
                </select>
            </div>
        `;
        
        document.getElementById('order-detail-modal').classList.remove('hidden');
    } catch (error) {
        console.error('Error loading order detail:', error);
        showToast('Error loading order details', 'error');
    }
}

// Update order status
async function updateOrderStatus(orderId, status) {
    if (!status) return;
    
    try {
        const response = await fetch(`/api/rmc/orders/${orderId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast('Order status updated!', 'success');
            closeModal('order-detail-modal');
            loadAllOrders();
        } else {
            showToast(result.error || 'Failed to update status', 'error');
        }
    } catch (error) {
        console.error('Error updating order status:', error);
        showToast('Error updating order status', 'error');
    }
}

// Show add client modal
function showAddClientModal() {
    document.getElementById('add-client-modal').classList.remove('hidden');
}

// Close modal
function closeModal(modalId) {
    document.getElementById(modalId).classList.add('hidden');
}

// Add client form
document.getElementById('add-client-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const clientData = {
        company_name: document.getElementById('client-company').value,
        contact_person: document.getElementById('client-contact').value,
        email: document.getElementById('client-email').value,
        phone: document.getElementById('client-phone').value,
        billing_address: document.getElementById('client-billing-address').value,
        shipping_address: document.getElementById('client-shipping-address').value,
        gst_number: document.getElementById('client-gst').value,
        credit_limit: parseFloat(document.getElementById('client-credit-limit').value) || 0
    };
    
    try {
        const response = await fetch('/api/rmc/clients', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(clientData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast('Client added successfully!', 'success');
            document.getElementById('add-client-form').reset();
            closeModal('add-client-modal');
            loadClients();
        } else {
            showToast(result.error || 'Failed to add client', 'error');
        }
    } catch (error) {
        console.error('Error adding client:', error);
        showToast('Error adding client', 'error');
    }
});

// Download invoice PDF
function downloadInvoicePDF(invoiceId) {
    window.open(`/api/rmc/invoice/${invoiceId}/pdf`, '_blank');
}

// Export functions
function exportOrders() {
    window.open('/api/rmc/export/orders', '_blank');
}

function exportInvoices() {
    window.open('/api/rmc/export/invoices', '_blank');
}

function exportPayments() {
    window.open('/api/rmc/export/payments', '_blank');
}

function exportClients() {
    // Create a simple Excel export for clients
    fetch('/api/rmc/clients')
        .then(res => res.json())
        .then(clients => {
            const wb = new ExcelJS.Workbook();
            const ws = wb.addWorksheet('Clients');
            
            ws.columns = [
                { header: 'Company Name', key: 'company_name' },
                { header: 'Contact Person', key: 'contact_person' },
                { header: 'Email', key: 'email' },
                { header: 'Phone', key: 'phone' },
                { header: 'Billing Address', key: 'billing_address' },
                { header: 'GST Number', key: 'gst_number' },
                { header: 'Credit Limit', key: 'credit_limit' },
                { header: 'Current Balance', key: 'current_balance' }
            ];
            
            clients.forEach(client => ws.addRow(client));
            
            wb.xlsx.writeBuffer().then(buffer => {
                const blob = new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'rmc_clients_export.xlsx';
                a.click();
            });
        });
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
    loadDashboard();
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
