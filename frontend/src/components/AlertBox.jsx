import React from 'react';
import { AlertCircle, CheckCircle2, Info, AlertTriangle } from 'lucide-react';

const icons = {
  info: <Info className="text-accent" size={24} />,
  success: <CheckCircle2 className="text-green-500" size={24} />,
  warning: <AlertTriangle className="text-yellow-500" size={24} />,
  error: <AlertCircle className="text-red-500" size={24} />,
};

const backgrounds = {
  info: 'bg-accent/10 border-accent/20 text-dark',
  success: 'bg-green-50 border-green-200 text-green-900',
  warning: 'bg-yellow-50 border-yellow-200 text-yellow-900',
  error: 'bg-red-50 border-red-200 text-red-900',
};

const AlertBox = ({ type = 'info', title, message, className = '' }) => {
  return (
    <div className={`flex items-start gap-4 p-4 rounded-2xl border ${backgrounds[type]} ${className} transition-all duration-300 hover:-translate-y-0.5`}>
      <div className="flex-shrink-0 mt-0.5">
        {icons[type]}
      </div>
      <div>
        {title && <h4 className="font-semibold mb-1">{title}</h4>}
        <p className="text-sm opacity-90">{message}</p>
      </div>
    </div>
  );
};

export default AlertBox;
