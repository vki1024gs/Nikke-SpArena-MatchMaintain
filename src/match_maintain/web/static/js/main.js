// Match Maintenance — 通用 JS

// Toast 通知
function showToast(message, type = 'info') {
    const colors = {
        info: '#6c8cff',
        success: '#4caf50',
        error: '#f44336',
        warning: '#ff9800',
    };
    
    const toast = document.createElement('div');
    toast.style.cssText = `
        position: fixed; bottom: 2rem; right: 2rem;
        background: ${colors[type] || colors.info}; color: #fff;
        padding: 1rem 1.5rem; border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        z-index: 9999; animation: slideIn 0.3s ease;
    `;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// 添加动画
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn { from { transform: translateX(100%); opacity: 0; } }
    @keyframes slideOut { from { transform: translateX(0); opacity: 1; } to { transform: translateX(100%); opacity: 0; } }
`;
document.head.appendChild(style);
