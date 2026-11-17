import React, { useState } from "react";

interface GpsButtonProps {
  onLocationFound: (lat: number, lon: number) => void;
  btnText: string;
  successText: string;
  failedText: string;
}

export const GpsButton: React.FC<GpsButtonProps> = ({
  onLocationFound,
  btnText,
  successText,
  failedText,
}) => {
  const [loading, setLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  const [isError, setIsError] = useState(false);

  const handleGetLocation = () => {
    if (!navigator.geolocation) {
      setIsError(true);
      setStatusMsg(failedText);
      return;
    }

    setLoading(true);
    setStatusMsg(null);
    setIsError(false);

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLoading(false);
        const lat = parseFloat(pos.coords.latitude.toFixed(6));
        const lon = parseFloat(pos.coords.longitude.toFixed(6));
        onLocationFound(lat, lon);
        setIsError(false);
        setStatusMsg(successText);
      },
      () => {
        setLoading(false);
        setIsError(true);
        setStatusMsg(failedText);
      },
      { timeout: 10000, enableHighAccuracy: true }
    );
  };

  return (
    <div className="flex flex-col gap-1.5">
      <button
        type="button"
        onClick={handleGetLocation}
        disabled={loading}
        className="inline-flex items-center justify-center gap-2 px-3 py-1.5 text-xs font-semibold text-emerald-800 bg-emerald-50 hover:bg-emerald-100 border border-emerald-300 rounded-md transition-colors"
      >
        <svg
          className={`w-4 h-4 ${loading ? "animate-spin" : ""}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
          />
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
          />
        </svg>
        {loading ? "..." : btnText}
      </button>
      {statusMsg && (
        <span
          className={`text-xs ${
            isError ? "text-amber-700 font-medium" : "text-emerald-700 font-medium"
          }`}
        >
          {statusMsg}
        </span>
      )}
    </div>
  );
};
