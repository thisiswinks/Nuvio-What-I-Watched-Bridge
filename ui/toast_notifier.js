/**
 * What I Watched Sync - Nielsen & A11y Toast Notifier
 * Non-disruptive, high-contrast toasts with aria-live="polite" and D-pad focus isolation.
 */
class ToastNotifier {
  static enabled = true;
  static density = 'all'; // 'all', 'warnings_errors', 'silent'

  static show(message, type = 'info', durationMs = 4000) {
    if (!ToastNotifier.enabled || ToastNotifier.density === 'silent') return;
    if (ToastNotifier.density === 'warnings_errors' && type === 'info') return;

    let container = document.getElementById('toast-container');
    if (!container && typeof document !== 'undefined') {
      container = document.createElement('div');
      container.id = 'toast-container';
      container.setAttribute('aria-live', 'polite');
      container.setAttribute('role', 'status');
      container.style.cssText = 'position: fixed; bottom: 24px; right: 24px; z-index: 9999; display: flex; flex-direction: column; gap: 10px; pointer-events: none;';
      document.body.appendChild(container);
    }
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type} glass-card`;
    toast.style.cssText = 'padding: 14px 22px; border-radius: 10px; color: #ffffff; background: rgba(15, 23, 42, 0.95); border: 1px solid rgba(255,255,255,0.15); box-shadow: 0 10px 25px rgba(0,0,0,0.5); font-family: system-ui, sans-serif; font-size: 14px; font-weight: 500; outline: 3px solid transparent; transition: all 0.3s ease;';
    toast.textContent = message;

    container.appendChild(toast);
    setTimeout(() => {
      if (toast.parentNode) {
        toast.parentNode.removeChild(toast);
      }
    }, durationMs);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = ToastNotifier;
}
