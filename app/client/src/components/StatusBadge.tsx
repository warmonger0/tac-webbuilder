import { statusColors } from '../config/theme';

interface StatusBadgeProps {
  status: string;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const getStatusColor = (status: string) => {
    const statusLower = status.toLowerCase();

    // Map status to theme colors
    if (statusLower.includes('plan')) {
      return `${statusColors.plan.bg} ${statusColors.plan.text}`;
    }
    if (statusLower.includes('build')) {
      return `${statusColors.build.bg} ${statusColors.build.text}`;
    }
    if (statusLower.includes('test')) {
      return `${statusColors.test.bg} ${statusColors.test.text}`;
    }
    if (statusLower.includes('review')) {
      return `${statusColors.review.bg} ${statusColors.review.text}`;
    }
    if (statusLower.includes('document')) {
      return `${statusColors.document.bg} ${statusColors.document.text}`;
    }
    if (statusLower.includes('ship')) {
      return `${statusColors.ship.bg} ${statusColors.ship.text}`;
    }
    if (statusLower.includes('completed') || statusLower.includes('success')) {
      return `${statusColors.completed.bg} ${statusColors.completed.text}`;
    }
    if (statusLower.includes('error') || statusLower.includes('failed')) {
      return `${statusColors.error.bg} ${statusColors.error.text}`;
    }
    if (statusLower.includes('pending')) {
      return `${statusColors.pending.bg} ${statusColors.pending.text}`;
    }

    return `${statusColors.pending.bg} ${statusColors.pending.text}`;
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
