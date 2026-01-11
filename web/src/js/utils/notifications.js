/**
 * Utility - Toast Notifications
 */

export function showNotification(message, type = 'info', duration = 3000) {
  const container = document.getElementById('notifications');
  if (!container) return;

  const notification = document.createElement('div');
  notification.className = `notification notification-${type}`;
  notification.textContent = message;

  container.appendChild(notification);

  // Auto-remove after duration
  setTimeout(() => {
    notification.classList.add('fade-out');
    setTimeout(() => notification.remove(), 300);
  }, duration);
}

export function showError(message) {
  showNotification(message, 'error', 5000);
}

export function showSuccess(message) {
  showNotification(message, 'success', 3000);
}

export function showInfo(message) {
  showNotification(message, 'info', 3000);
}
