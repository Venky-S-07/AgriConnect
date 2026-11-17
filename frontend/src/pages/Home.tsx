import React from 'react';
import { StatusBadge } from '../components/StatusBadge';
import { Droplet, CloudSun, ShieldCheck, TrendingUp, Check, Layers, ArrowRight } from 'lucide-react';
import { FarmerProfile } from '../services/api';

interface HomeProps {
  translations: Record<string, string>;
  farmer?: FarmerProfile | null;
  onOpenAuth: () => void;
  onOpenDashboard: () => void;
}

export const Home: React.FC<HomeProps> = ({
  translations,
  farmer,
  onOpenAuth,
  onOpenDashboard,
}) => {
  return (
    <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8 space-y-6">
      {/* Live Backend Connection Status Indicator */}
      <StatusBadge translations={translations} />

      {/* Hero Section */}
      <section className="bg-gradient-to-br from-emerald-950 via-emerald-900 to-green-900 rounded-2xl p-6 sm:p-10 text-white shadow-xl relative overflow-hidden">
        <div className="max-w-3xl space-y-5 relative z-10">
          <div className="inline-flex items-center gap-2 bg-emerald-500/20 border border-emerald-400/30 px-3 py-1 rounded-full text-xs font-semibold text-emerald-200">
            <Layers className="w-3.5 h-3.5" />
            <span>Milestone 2 — Farmer Onboarding & Farm Setup</span>
          </div>

          <h1 className="text-2xl sm:text-4xl font-extrabold tracking-tight leading-tight">
            {translations.hero_title}
          </h1>

          <p className="text-sm sm:text-base text-emerald-100 leading-relaxed font-light">
            {translations.hero_desc}
          </p>

          <div className="pt-2 flex flex-wrap items-center gap-4">
            {farmer ? (
              <button
                onClick={onOpenDashboard}
                className="inline-flex items-center gap-2 px-5 py-2.5 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold rounded-xl shadow-lg transition-all"
              >
                <span>{translations.btn_dashboard}</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            ) : (
              <button
                onClick={onOpenAuth}
                className="inline-flex items-center gap-2 px-5 py-2.5 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold rounded-xl shadow-lg transition-all"
              >
                <span>{translations.btn_get_started}</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            )}

            <div className="text-xs text-emerald-200/90 flex items-center gap-2">
              <Check className="w-4 h-4 text-emerald-400" />
              <span>Bilingual (EN / ಕನ್ನಡ) • Privacy-Preserving DPDP Consent</span>
            </div>
          </div>
        </div>
      </section>

      {/* Architectural Pillars Preview (Cards) */}
      <section className="space-y-4">
        <h2 className="text-lg font-bold text-gray-900 tracking-tight">
          {translations.features_title}
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Card 1: Irrigation */}
          <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm hover:shadow-md transition-shadow space-y-3">
            <div className="w-10 h-10 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center font-bold">
              <Droplet className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-gray-900">
              {translations.feature_irrigation_title}
            </h3>
            <p className="text-xs text-gray-600 leading-relaxed">
              {translations.feature_irrigation_desc}
            </p>
            <span className="inline-block text-[10px] uppercase font-semibold text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-100">
              Deterministic FAO-56
            </span>
          </div>

          {/* Card 2: Weather */}
          <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm hover:shadow-md transition-shadow space-y-3">
            <div className="w-10 h-10 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center font-bold">
              <CloudSun className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-gray-900">
              {translations.feature_weather_title}
            </h3>
            <p className="text-xs text-gray-600 leading-relaxed">
              {translations.feature_weather_desc}
            </p>
            <span className="inline-block text-[10px] uppercase font-semibold text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-100">
              Open-Meteo + IMD
            </span>
          </div>

          {/* Card 3: Disease */}
          <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm hover:shadow-md transition-shadow space-y-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center font-bold">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-gray-900">
              {translations.feature_disease_title}
            </h3>
            <p className="text-xs text-gray-600 leading-relaxed">
              {translations.feature_disease_desc}
            </p>
            <span className="inline-block text-[10px] uppercase font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-100">
              Validated ICAR SOPs
            </span>
          </div>

          {/* Card 4: Market Intelligence */}
          <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm hover:shadow-md transition-shadow space-y-3">
            <div className="w-10 h-10 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center font-bold">
              <TrendingUp className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-gray-900">
              {translations.feature_market_title}
            </h3>
            <p className="text-xs text-gray-600 leading-relaxed">
              {translations.feature_market_desc}
            </p>
            <span className="inline-block text-[10px] uppercase font-semibold text-purple-700 bg-purple-50 px-2 py-0.5 rounded border border-purple-100">
              Agmarknet Mandi Feeds
            </span>
          </div>
        </div>
      </section>
    </main>
  );
};
