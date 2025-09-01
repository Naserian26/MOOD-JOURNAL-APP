// Chart initialization and interaction
document.addEventListener('DOMContentLoaded', function() {
    const chartCtx = document.getElementById('moodChart');
    const timeRangeSelect = document.getElementById('timeRange');
    
    if (chartCtx) {
        const ctx = chartCtx.getContext('2d');
        let moodChart;
        
        function loadChart(days = 30) {
            fetch(`/chart-data?days=${days}`)
                .then(response => response.json())
                .then(data => {
                    if (moodChart) {
                        moodChart.destroy();
                    }
                    
                    moodChart = new Chart(ctx, {
                        type: 'line',
                        data: data,
                        options: {
                            responsive: true,
                            scales: {
                                y: {
                                    beginAtZero: true,
                                    max: 100,
                                    title: {
                                        display: true,
                                        text: 'Mood Intensity (%)'
                                    }
                                }
                            },
                            plugins: {
                                tooltip: {
                                    callbacks: {
                                        label: function(context) {
                                            return context.dataset.label + ': ' + context.parsed.y.toFixed(1) + '%';
                                        }
                                    }
                                }
                            }
                        }
                    });
                });
        }
        
        loadChart();
        
        if (timeRangeSelect) {
            timeRangeSelect.addEventListener('change', function() {
                loadChart(this.value);
            });
        }
    }
    
    // Paystack checkout
    const payButtons = document.querySelectorAll('.pay-btn');
    if (payButtons.length > 0) {
        payButtons.forEach(button => {
            button.addEventListener('click', async () => {
                const plan = button.getAttribute('data-plan');
                const amount = button.getAttribute('data-amount');
                
                // Disable button to prevent multiple clicks
                button.disabled = true;
                button.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
                
                try {
                    const response = await fetch('/initiate-payment', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            amount: amount,
                            plan: plan
                        }),
                    });
                    
                    const data = await response.json();
                    
                    if (data.status) {
                        // Open Paystack payment modal
                        const handler = PaystackPop.setup({
                            key: button.getAttribute('data-key'),
                            email: button.getAttribute('data-email'),
                            amount: data.data.amount,
                            currency: 'NGN',
                            ref: data.data.reference,
                            callback: function(response) {
                                // Redirect to verification page
                                window.location.href = `/verify-payment?reference=${response.reference}`;
                            },
                            onClose: function() {
                                // Re-enable button if payment is closed
                                button.disabled = false;
                                button.innerHTML = 'Upgrade Now';
                            }
                        });
                        handler.openIframe();
                    } else {
                        alert('Payment initialization failed: ' + data.message);
                        button.disabled = false;
                        button.innerHTML = 'Upgrade Now';
                    }
                } catch (error) {
                    console.error('Error:', error);
                    alert('An error occurred. Please try again.');
                    button.disabled = false;
                    button.innerHTML = 'Upgrade Now';
                }
            });
        });
    }
});