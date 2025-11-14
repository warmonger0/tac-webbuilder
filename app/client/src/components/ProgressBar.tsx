interface ProgressBarProps {
  phases: string[];
  current: string;
}

export function ProgressBar({ phases, current }: ProgressBarProps) {
  const currentIndex = phases.findIndex(
    (phase) => phase.toLowerCase() === current.toLowerCase()
  );

  return (
    <div className="w-full">
      <div className="flex items-center justify-between">
        {phases.map((phase, index) => {
          const isCompleted = index < currentIndex;
          const isCurrent = index === currentIndex;

          return (
            <div key={phase} className="flex-1 flex items-center">
              <div className="flex flex-col items-center flex-1">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium ${
                    isCompleted
                      ? 'bg-green-500 text-white'
                      : isCurrent
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-200 text-gray-500'
                  }`}
                >
                  {isCompleted ? '✓' : index + 1}
                </div>
                <span
                  className={`text-xs mt-1 ${
                    isCurrent ? 'font-medium text-gray-900' : 'text-gray-500'
                  }`}
                >
                  {phase}
                </span>
              </div>
              {index < phases.length - 1 && (
                <div
                  className={`h-1 flex-1 ${
                    isCompleted ? 'bg-green-500' : 'bg-gray-200'
                  }`}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
