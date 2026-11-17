import React, { useEffect, useState } from 'react';
import { CheckCircle2, AlertCircle, RefreshCw } from 'lucide-react';

interface BackendHealthData {
  status: string;
  app: string;
  version: string;
  milestone: string;
}

interface StatusBadgeProps {
  translations: Record<string, string>;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ translations }) => {
  const [health, setHealth] = useState<BackendHealthData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const checkHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/v1/health');
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data: BackendHealthData = await response.json();
      setHealth(data);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Connection failed';
      setError(message);
      setHealth(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkHealth();
    // Poll every 15 seconds to keep connection state updated
    const interval = setInterval(checkHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bg-white rounded-xl p-4 sm:p-5 border border-gray-200 shadow-sm transition-all">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center space-x-3">
          {loading ? (
            <div className="p-2 bg-blue-50 text-blue-600 rounded-lg animate-spin">
              <RefreshCw className="w-5 h-5" />
            </div>
          ) : health && health.status === 'ok' ? (
            <div className="p-2 bg-green-50 text-green-600 rounded-lg">
              <CheckCircle2 className="w-5 h-5" />
            </div>
          ) : (
            <div className="p-2 bg-amber-50 text-amber-600 rounded-lg">
              <AlertCircle className="w-5 h-5" />
            </div>
          )}

          <div>
            <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
              {translations.backend_status}
            </div>
            <div className="text-sm font-bold text-gray-900 flex items-center gap-2 mt-0.5">
              {health && health.status === 'ok' ? (
                <span className="text-green-700 font-semibold flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-green-500 inline-block animate-pulse"></span>
                  {translations.connected} — {health.app} v{health.version}
                </span>
              ) : (
                <span className="text-amber-700 font-medium">
                  {translations.disconnected} {error ? `(${error})` : ''}
                </span>
              )}
            </div>
            {health && (
              <div className="text-xs text-gray-500 mt-1">
                {health.milestone}
              </div>
            )}
          </div>
        </div>

        <button
          onClick={checkHealth}
          disabled={loading}
          className="self-start sm:self-auto text-xs px-3 py-1.5 rounded-lg border border-gray-300 hover:bg-gray-50 text-gray-700 font-medium transition-colors flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>
    </div>
  );
};
