interface ScoreCardProps {
  title: string;
  score: number; // 0-100
  description: string;
}

type ColorKey = 'green' | 'blue' | 'yellow' | 'orange';

export function ScoreCard({ title, score, description }: ScoreCardProps) {
  // Determine color based on score
  const getScoreColor = (score: number): ColorKey => {
    if (score >= 90) return 'green';
    if (score >= 70) return 'blue';
    if (score >= 50) return 'yellow';
    return 'orange';
  };

  const color = getScoreColor(score);

  // Color classes for different states
  const colorClasses = {
    green: {
      bg: 'bg-green-50',
      border: 'border-green-200',
      text: 'text-green-800',
      progress: 'text-green-700',
      ring: 'stroke-green-600',
      track: 'stroke-green-200',
    },
    blue: {
      bg: 'bg-blue-50',
      border: 'border-blue-200',
      text: 'text-blue-800',
      progress: 'text-blue-700',
      ring: 'stroke-blue-600',
      track: 'stroke-blue-200',
    },
    yellow: {
      bg: 'bg-yellow-50',
      border: 'border-yellow-200',
      text: 'text-yellow-800',
      progress: 'text-yellow-700',
      ring: 'stroke-yellow-600',
      track: 'stroke-yellow-200',
    },
    orange: {
      bg: 'bg-orange-50',
      border: 'border-orange-200',
      text: 'text-orange-800',
      progress: 'text-orange-700',
      ring: 'stroke-orange-600',
      track: 'stroke-orange-200',
    },
  };

  const classes = colorClasses[color];

  // Calculate circle progress
  const radius = 40;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  return (
    <div className={`${classes.bg} ${classes.border} border rounded-lg p-4 flex flex-col items-center`}>
      {/* Title */}
      <h4 className={`text-sm font-semibold ${classes.text} mb-3`}>
        {title}
      </h4>

      {/* Circular Progress Indicator */}
      <div className="relative w-24 h-24 mb-3">
        <svg className="transform -rotate-90 w-24 h-24">
          {/* Background circle */}
          <circle
            cx="48"
            cy="48"
            r={radius}
            className={classes.track}
            strokeWidth="8"
            fill="none"
          />
          {/* Progress circle */}
          <circle
            cx="48"
            cy="48"
            r={radius}
            className={classes.ring}
            strokeWidth="8"
            fill="none"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            style={{ transition: 'stroke-dashoffset 0.5s ease' }}
          />
        </svg>

        {/* Score text in center */}
        <div className="absolute inset-0 flex items-center justify-center">
          <span className={`text-2xl font-bold ${classes.progress}`}>
            {Math.round(score)}
          </span>
        </div>
      </div>

      {/* Description */}
      <p className={`text-xs text-center ${classes.text} opacity-75`}>
        {description}
      </p>
    </div>
  );
}
