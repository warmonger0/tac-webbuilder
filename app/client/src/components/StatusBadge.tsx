interface StatusBadgeProps {
  status: string;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const getStatusColor = (status: string) => {
    const statusLower = status.toLowerCase();

    if (statusLower.includes('plan')) return 'bg-blue-100 text-blue-800';
    if (statusLower.includes('build')) return 'bg-purple-100 text-purple-800';
    if (statusLower.includes('test')) return 'bg-yellow-100 text-yellow-800';
    if (statusLower.includes('review')) return 'bg-orange-100 text-orange-800';
    if (statusLower.includes('document')) return 'bg-indigo-100 text-indigo-800';
    if (statusLower.includes('ship')) return 'bg-green-100 text-green-800';
    if (statusLower.includes('completed') || statusLower.includes('success')) {
      return 'bg-green-100 text-green-800';
    }
    if (statusLower.includes('error') || statusLower.includes('failed')) {
      return 'bg-red-100 text-red-800';
    }
    if (statusLower.includes('pending')) return 'bg-gray-100 text-gray-800';

    return 'bg-gray-100 text-gray-800';
  };

  return (
    <span
      className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(
        status
      )}`}
    >
      {status}
    </span>
  );
}
