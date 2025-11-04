import { RiskLevel } from '../types';
import { Badge } from './ui/badge';
import { AlertCircle, AlertTriangle, CheckCircle } from 'lucide-react';

interface RiskBadgeProps {
  level: RiskLevel;
  showIcon?: boolean;
}

export function RiskBadge({ level, showIcon = true }: RiskBadgeProps) {
  const config = {
    high: {
      label: 'Alto Riesgo',
      className: 'bg-red-100 text-red-800 border-red-300',
      icon: AlertCircle
    },
    medium: {
      label: 'Riesgo Medio',
      className: 'bg-yellow-100 text-yellow-800 border-yellow-300',
      icon: AlertTriangle
    },
    low: {
      label: 'Bajo Riesgo',
      className: 'bg-green-100 text-green-800 border-green-300',
      icon: CheckCircle
    }
  };

  const { label, className, icon: Icon } = config[level];

  return (
    <Badge variant="outline" className={className}>
      {showIcon && <Icon className="w-3 h-3 mr-1" />}
      {label}
    </Badge>
  );
}
