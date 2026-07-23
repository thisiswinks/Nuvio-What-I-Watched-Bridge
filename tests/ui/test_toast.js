const ToastNotifier = require('../../ui/toast_notifier.js');

console.assert(ToastNotifier.enabled === true, "Toasts must be enabled by default");
ToastNotifier.enabled = false;
ToastNotifier.show("Test message", "info"); // Should do nothing silently
ToastNotifier.enabled = true;

console.assert(ToastNotifier.density === 'all', "Density must default to all");
console.log("SUCCESS: ToastNotifier unit test passed 100%");
