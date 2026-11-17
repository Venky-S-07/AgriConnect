import React from 'react';
import { Sprout, Globe, User, LogOut } from 'lucide-react';
import { FarmerProfile } from '../services/api';

interface NavbarProps {
  currentLang: string;
  onLanguageChange: (lang: string) => void;
  translations: Record<string, string>;
  farmer?: FarmerProfile | null;
  onLogout?: () => void;
  onOpenAuth?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentLang,
  onLanguageChange,
  translations,
  farmer,
  onLogout,
  onOpenAuth,
}) => {
  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-40 shadow-sm">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand Logo & Title */}
          <div className="flex items-center space-x-3">
            <div className="bg-emerald-700 p-2 rounded-xl text-white shadow-sm flex items-center justify-center">
              <Sprout className="w-6 h-6" />
            </div>
            <div>
              <span className="text-xl font-bold text-gray-900 tracking-tight block">
                {translations.app_name || 'AgriConnect'}
              </span>
              <span className="text-xs text-gray-500 hidden sm:block">
                {translations.app_tagline}
              </span>
            </div>
          </div>

          {/* Right Action Controls */}
          <div className="flex items-center space-x-3">
            {farmer ? (
              <div className="flex items-center space-x-2">
                <div className="hidden sm:flex items-center gap-1.5 px-3 py-1 bg-emerald-50 border border-emerald-200 rounded-lg text-xs font-semibold text-emerald-800">
                  <User className="w-3.5 h-3.5" />
                  <span>{farmer.full_name || farmer.phone_number}</span>
                </div>
                {onLogout && (
                  <button
                    onClick={onLogout}
                    title={translations.btn_logout || "Logout"}
                    className="p-1.5 text-gray-500 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors"
                  >
                    <LogOut className="w-4 h-4" />
                  </button>
                )}
              </div>
            ) : (
              onOpenAuth && (
                <button
                  onClick={onOpenAuth}
                  className="px-3.5 py-1.5 text-xs font-semibold bg-emerald-700 hover:bg-emerald-800 text-white rounded-lg transition-colors shadow-sm"
                >
                  {translations.btn_get_started || "Login / Sign up"}
                </button>
              )
            )}

            {/* Language Selector Dropdown */}
            <div className="flex items-center space-x-2 bg-gray-100 hover:bg-gray-200 transition-colors rounded-lg px-2.5 py-1.5 border border-gray-200">
              <Globe className="w-4 h-4 text-gray-600" />
              <label htmlFor="lang-select" className="sr-only">
                {translations.language}
              </label>
              <select
                id="lang-select"
                value={currentLang}
                onChange={(e) => onLanguageChange(e.target.value)}
                className="bg-transparent text-xs font-semibold text-gray-800 focus:outline-none cursor-pointer"
              >
                <option value="en">English (EN)</option>
                <option value="kn">ಕನ್ನಡ (KN)</option>
              </select>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
