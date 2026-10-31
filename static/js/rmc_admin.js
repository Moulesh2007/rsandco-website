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
    if (tabName === 'quotations') loadQuotations();
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

// ==========================================
// QUOTATIONS MODULE
// ==========================================
let quotationItemCount = 0;
let currentQuotationId = null;

async function loadQuotations() {
    const container = document.getElementById('quotations-list');
    container.innerHTML = '<div class="loading-spinner"></div>';
    
    try {
        const response = await fetch('/api/rmc/quotations');
        const quotations = await response.json();
        
        if (quotations.length === 0) {
            container.innerHTML = '<p style="color: var(--text-gray); text-align: center; padding: 40px;">No quotations found.</p>';
            return;
        }
        
        container.innerHTML = quotations.map(q => `
            <div class="rmc-list-item" onclick="viewQuotation('${q.id}')">
                <div class="item-main">
                    <div class="item-title">${q.quotation_number}</div>
                    <div class="item-subtitle">${q.quotation_date} | Validity: ${q.validity_days} Days</div>
                    <div class="item-meta">
                        <span>To: <strong>${q.company_name}</strong></span>
                        <span>Total: <strong>₹${q.grand_total?.toLocaleString() || '0'}</strong></span>
                    </div>
                </div>
                <div class="item-actions">
                    <span class="item-status status-${q.status?.toLowerCase().replace(' ', '-')}">${q.status}</span>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading quotations:', error);
        container.innerHTML = '<p style="color: var(--danger); text-align: center;">Error loading quotations.</p>';
    }
}

async function showAddQuotationModal() {
    document.getElementById('add-quotation-form').reset();
    document.getElementById('q-date').valueAsDate = new Date();
    document.getElementById('q-items-body').innerHTML = '';
    quotationItemCount = 0;
    addQuotationItem(); // Add one empty row
    calculateQuotationTotals();
    
    // Load clients for dropdown
    try {
        const response = await fetch('/api/rmc/clients');
        const clients = await response.json();
        const select = document.getElementById('q-client-select');
        select.innerHTML = '<option value="">-- Custom / New Client --</option>' + 
            clients.map(c => `<option value="${c.id}">${c.company_name} (${c.contact_person})</option>`).join('');
    } catch (e) {
        console.error('Error loading clients for dropdown', e);
    }
    
    document.getElementById('add-quotation-modal').classList.remove('hidden');
}

async function fillClientDetailsForQuotation(clientId) {
    if (!clientId) {
        document.getElementById('q-company-name').value = '';
        document.getElementById('q-client-name').value = '';
        document.getElementById('q-email').value = '';
        document.getElementById('q-phone').value = '';
        document.getElementById('q-address').value = '';
        document.getElementById('q-gst-number').value = '';
        return;
    }
    
    try {
        const response = await fetch('/api/rmc/clients');
        const clients = await response.json();
        const client = clients.find(c => c.id === clientId);
        
        if (client) {
            document.getElementById('q-company-name').value = client.company_name || '';
            document.getElementById('q-client-name').value = client.contact_person || '';
            document.getElementById('q-email').value = client.email || '';
            document.getElementById('q-phone').value = client.phone || '';
            document.getElementById('q-address').value = client.billing_address || '';
            document.getElementById('q-gst-number').value = client.gst_number || '';
        }
    } catch (e) {
        console.error(e);
    }
}

function addQuotationItem() {
    quotationItemCount++;
    const tbody = document.getElementById('q-items-body');
    const tr = document.createElement('tr');
    tr.id = `q-item-row-${quotationItemCount}`;
    tr.innerHTML = `
        <td><input type="text" class="q-item-desc" required style="width:100%;" placeholder="e.g. M20 Grade Concrete"></td>
        <td><input type="number" class="q-item-qty" required style="width:100%;" min="0" step="0.01" value="0" onchange="calculateQuotationTotals()"></td>
        <td><input type="text" class="q-item-unit" style="width:100%;" value="cu.m"></td>
        <td><input type="number" class="q-item-rate" required style="width:100%;" min="0" step="0.01" value="0" onchange="calculateQuotationTotals()"></td>
        <td><input type="number" class="q-item-amount" readonly style="width:100%; background:#222; border:none; color:#D4AF37;"></td>
        <td><button type="button" class="btn-outline" style="padding:5px 10px; color:#f44336; border-color:#f44336;" onclick="removeQuotationItem(${quotationItemCount})">X</button></td>
    `;
    tbody.appendChild(tr);
}

function removeQuotationItem(id) {
    const row = document.getElementById(`q-item-row-${id}`);
    if (row) {
        row.remove();
        calculateQuotationTotals();
    }
}

function calculateQuotationTotals() {
    let subtotal = 0;
    const rows = document.getElementById('q-items-body').children;
    
    for (let row of rows) {
        const qty = parseFloat(row.querySelector('.q-item-qty').value) || 0;
        const rate = parseFloat(row.querySelector('.q-item-rate').value) || 0;
        const amount = qty * rate;
        row.querySelector('.q-item-amount').value = amount.toFixed(2);
        subtotal += amount;
    }
    
    document.getElementById('q-subtotal').textContent = `₹ ${subtotal.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    
    const includeGst = document.getElementById('q-include-gst').checked;
    const gstTypeContainer = document.getElementById('q-gst-type-container');
    const gstDetails = document.getElementById('q-gst-details');
    
    let grandTotal = subtotal;
    
    if (includeGst) {
        gstTypeContainer.classList.remove('hidden');
        gstDetails.classList.remove('hidden');
        
        const gstType = document.querySelector('input[name="q_gst_type"]:checked').value;
        const cgstRow = document.getElementById('q-cgst-row');
        const sgstRow = document.getElementById('q-sgst-row');
        const igstRow = document.getElementById('q-igst-row');
        
        if (gstType === 'intra') {
            cgstRow.classList.remove('hidden');
            sgstRow.classList.remove('hidden');
            igstRow.classList.add('hidden');
            
            const cgst = subtotal * 0.09;
            const sgst = subtotal * 0.09;
            document.getElementById('q-cgst').textContent = `₹ ${cgst.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
            document.getElementById('q-sgst').textContent = `₹ ${sgst.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
            
            grandTotal = subtotal + cgst + sgst;
        } else {
            cgstRow.classList.add('hidden');
            sgstRow.classList.add('hidden');
            igstRow.classList.remove('hidden');
            
            const igst = subtotal * 0.18;
            document.getElementById('q-igst').textContent = `₹ ${igst.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
            
            grandTotal = subtotal + igst;
        }
    } else {
        gstTypeContainer.classList.add('hidden');
        gstDetails.classList.add('hidden');
    }
    
    document.getElementById('q-grand-total').textContent = `₹ ${grandTotal.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    
    return { subtotal, grandTotal };
}

document.getElementById('add-quotation-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const items = [];
    const rows = document.getElementById('q-items-body').children;
    for (let row of rows) {
        items.push({
            description: row.querySelector('.q-item-desc').value,
            quantity: parseFloat(row.querySelector('.q-item-qty').value) || 0,
            unit: row.querySelector('.q-item-unit').value,
            rate: parseFloat(row.querySelector('.q-item-rate').value) || 0,
            amount: parseFloat(row.querySelector('.q-item-amount').value) || 0
        });
    }
    
    if (items.length === 0) {
        showToast('Please add at least one item.', 'error');
        return;
    }
    
    const totals = calculateQuotationTotals();
    const includeGst = document.getElementById('q-include-gst').checked;
    const gstType = document.querySelector('input[name="q_gst_type"]:checked').value;
    
    let cgst = 0, sgst = 0, igst = 0;
    if (includeGst) {
        if (gstType === 'intra') {
            cgst = totals.subtotal * 0.09;
            sgst = totals.subtotal * 0.09;
        } else {
            igst = totals.subtotal * 0.18;
        }
    }
    
    // Fetch default T&C
    let terms = [];
    try {
        const setRes = await fetch('/api/rmc/quotation-settings');
        const settings = await setRes.json();
        terms = settings.default_terms ? JSON.parse(settings.default_terms) : [];
    } catch(e) {}
    
    const data = {
        client_id: document.getElementById('q-client-select').value || null,
        company_name: document.getElementById('q-company-name').value,
        client_name: document.getElementById('q-client-name').value,
        email: document.getElementById('q-email').value,
        phone: document.getElementById('q-phone').value,
        address: document.getElementById('q-address').value,
        client_gst_number: document.getElementById('q-gst-number').value,
        quotation_date: document.getElementById('q-date').value,
        validity_days: parseInt(document.getElementById('q-validity').value) || 15,
        include_gst: includeGst,
        gst_type: gstType,
        subtotal: totals.subtotal,
        cgst_amount: cgst,
        sgst_amount: sgst,
        igst_amount: igst,
        grand_total: totals.grandTotal,
        notes: document.getElementById('q-notes').value,
        items: items,
        terms_and_conditions: terms
    };
    
    try {
        const response = await fetch('/api/rmc/quotations', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        if (result.success) {
            showToast(`Quotation ${result.quotation_number} generated!`, 'success');
            closeModal('add-quotation-modal');
            loadQuotations();
        } else {
            showToast('Failed to generate quotation', 'error');
        }
    } catch (error) {
        console.error(error);
        showToast('Error generating quotation', 'error');
    }
});

async function viewQuotation(id) {
    currentQuotationId = id;
    try {
        const response = await fetch(`/api/rmc/quotations/${id}`);
        const q = await response.json();
        
        let itemsHtml = q.items.map(i => `
            <tr>
                <td>${i.description}</td>
                <td>${i.quantity}</td>
                <td>${i.unit}</td>
                <td>₹${i.rate.toLocaleString()}</td>
                <td>₹${i.amount.toLocaleString()}</td>
            </tr>
        `).join('');
        
        let gstHtml = '';
        if (q.include_gst) {
            if (q.gst_type === 'intra') {
                gstHtml = `
                    <div class="detail-row"><span>CGST (9%):</span><span>₹${q.cgst_amount?.toLocaleString() || '0'}</span></div>
                    <div class="detail-row"><span>SGST (9%):</span><span>₹${q.sgst_amount?.toLocaleString() || '0'}</span></div>
                `;
            } else {
                gstHtml = `
                    <div class="detail-row"><span>IGST (18%):</span><span>₹${q.igst_amount?.toLocaleString() || '0'}</span></div>
                `;
            }
        }
        
        const content = document.getElementById('view-quotation-content');
        content.innerHTML = `
            <div class="detail-section">
                <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
                    <h4>Quotation Details</h4>
                    <span class="item-status status-${q.status?.toLowerCase().replace(' ', '-')}">${q.status}</span>
                </div>
                <div class="detail-row"><span>Number:</span><span><strong>${q.quotation_number}</strong></span></div>
                <div class="detail-row"><span>Date:</span><span>${q.quotation_date}</span></div>
                <div class="detail-row"><span>Validity:</span><span>${q.validity_days} Days (Until ${q.validity_date})</span></div>
                <div class="detail-row"><span>To:</span><span>${q.company_name}</span></div>
                <div class="detail-row"><span>Phone:</span><span>${q.phone}</span></div>
                <div class="detail-row"><span>Email:</span><span>${q.email || 'N/A'}</span></div>
                <div class="detail-row"><span>Address:</span><span>${q.address}</span></div>
                ${q.client_gst_number ? `<div class="detail-row"><span>GSTIN:</span><span>${q.client_gst_number}</span></div>` : ''}
            </div>
            
            <div class="detail-section" style="margin-top:20px;">
                <h4>Line Items</h4>
                <table class="order-items-table" style="width:100%;">
                    <thead>
                        <tr>
                            <th>Description</th>
                            <th>Qty</th>
                            <th>Unit</th>
                            <th>Rate</th>
                            <th>Amount</th>
                        </tr>
                    </thead>
                    <tbody>${itemsHtml}</tbody>
                </table>
            </div>
            
            <div class="detail-section" style="margin-top:20px; border-top:1px solid #333; padding-top:15px; text-align:right;">
                <div class="detail-row" style="justify-content:flex-end; gap:20px;"><span>Subtotal:</span><span>₹${q.subtotal?.toLocaleString() || '0'}</span></div>
                ${gstHtml}
                <div class="detail-row" style="justify-content:flex-end; gap:20px; font-size:1.2em; color:#D4AF37; font-weight:bold; margin-top:10px;">
                    <span>Grand Total:</span><span>₹${q.grand_total?.toLocaleString() || '0'}</span>
                </div>
            </div>
        `;
        
        const btnConvert = document.getElementById('btn-convert-invoice');
        if (q.status === 'Converted') {
            btnConvert.style.display = 'none';
        } else {
            btnConvert.style.display = 'block';
        }
        
        document.getElementById('view-quotation-modal').classList.remove('hidden');
    } catch (e) {
        console.error(e);
        showToast('Error loading quotation details', 'error');
    }
}

function openQuotationPdf() {
    if (currentQuotationId) {
        window.open(`/api/rmc/quotations/${currentQuotationId}/pdf`, '_blank');
    }
}

async function convertQuotationToInvoice() {
    if (!currentQuotationId) return;
    if (!confirm('Convert this Quotation into a confirmed Order and auto-generate an Invoice?')) return;
    
    try {
        const response = await fetch(`/api/rmc/quotations/${currentQuotationId}/convert-to-invoice`, {
            method: 'POST'
        });
        const result = await response.json();
        
        if (result.success) {
            showToast('Quotation converted to Order & Invoice!', 'success');
            closeModal('view-quotation-modal');
            loadQuotations();
        } else {
            showToast(result.error || 'Conversion failed', 'error');
        }
    } catch (e) {
        showToast('Error during conversion', 'error');
    }
}

async function deleteQuotation() {
    if (!currentQuotationId) return;
    if (!confirm('Are you sure you want to delete this quotation?')) return;
    
    try {
        const response = await fetch(`/api/rmc/quotations/${currentQuotationId}`, {
            method: 'DELETE'
        });
        const result = await response.json();
        
        if (result.success) {
            showToast('Quotation deleted', 'success');
            closeModal('view-quotation-modal');
            loadQuotations();
        } else {
            showToast('Failed to delete', 'error');
        }
    } catch (e) {
        showToast('Error deleting quotation', 'error');
    }
}

async function showQuotationSettingsModal() {
    try {
        const res = await fetch('/api/rmc/quotation-settings');
        const set = await res.json();
        
        document.getElementById('qs-default-validity').value = set.default_validity_days || 15;
        let terms = [];
        if (set.default_terms) {
            try { terms = JSON.parse(set.default_terms); } catch(e){}
        }
        document.getElementById('qs-default-terms').value = terms.join('\n');
        
        document.getElementById('quotation-settings-modal').classList.remove('hidden');
    } catch (e) {
        showToast('Error loading settings', 'error');
    }
}

document.getElementById('quotation-settings-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const val = parseInt(document.getElementById('qs-default-validity').value) || 15;
    const terms = document.getElementById('qs-default-terms').value.split('\n').map(t => t.trim()).filter(t => t);
    
    try {
        const response = await fetch('/api/rmc/quotation-settings', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                default_validity_days: val,
                default_terms: terms
            })
        });
        
        if (response.ok) {
            showToast('Settings saved successfully', 'success');
            closeModal('quotation-settings-modal');
        } else {
            showToast('Failed to save settings', 'error');
        }
    } catch(e) {
        showToast('Error saving settings', 'error');
    }
});
// ==========================================

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
