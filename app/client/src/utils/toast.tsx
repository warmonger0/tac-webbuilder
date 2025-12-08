import toast from 'react-hot-toast';

export const showSuccess = (message: string) => {
  toast.success(message);
};

export const showError = (message: string) => {
  toast.error(message);
};

export const showInfo = (message: string) => {
  toast(message, {
    icon: 'ℹ️',
  });
};

export const showConfirm = (
  message: string,
  onConfirm: () => void,
  onCancel?: () => void
) => {
  toast((t) => (
    <div>
      <p className="mb-3">{message}</p>
      <div className="flex gap-2">
        <button
          onClick={() => {
            onConfirm();
            toast.dismiss(t.id);
          }}
          className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Confirm
        </button>
        <button
          onClick={() => {
            onCancel?.();
            toast.dismiss(t.id);
          }}
          className="px-3 py-1 bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
        >
          Cancel
        </button>
      </div>
    </div>
  ), {
    duration: Infinity,
    icon: '❓',
  });
};
