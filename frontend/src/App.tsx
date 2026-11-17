import { useEffect, useState } from 'react';
import { Navbar } from './components/Navbar';
import { Home } from './pages/Home';
import { AuthModal } from './pages/AuthModal';
import { FarmSetupWizard } from './pages/FarmSetupWizard';
import { Dashboard } from './pages/Dashboard';
import { api, clearAuthToken, FarmerProfile, getAuthToken } from './services/api';
import enTranslations from './locales/en.json';
import knTranslations from './locales/kn.json';

const translationsMap: Record<string, Record<string, string>> = {
  en: enTranslations,
  kn: knTranslations,
};

export default function App() {
  const [currentLang, setCurrentLang] = useState<string>('kn');
  const [farmer, setFarmer] = useState<FarmerProfile | null>(null);
  const [view, setView] = useState<'home' | 'dashboard' | 'wizard'>('home');
  const [isAuthOpen, setIsAuthOpen] = useState(false);

  const t = (key: string): string => {
    const dict = translationsMap[currentLang] || translationsMap.en;
    return dict[key] || translationsMap.en[key] || key;
  };

  // Restore authenticated session on mount
  useEffect(() => {
    const token = getAuthToken();
    if (token) {
      api
        .getMe()
        .then((f) => {
          setFarmer(f);
          if (!f.has_farms) {
            setView('wizard');
          } else {
            setView('dashboard');
          }
        })
        .catch(() => {
          clearAuthToken();
          setFarmer(null);
          setView('home');
        });
    }
  }, []);

  const handleLoginSuccess = (profile: FarmerProfile) => {
    setFarmer(profile);
    if (!profile.has_farms) {
      setView('wizard');
    } else {
      setView('dashboard');
    }
  };

  const handleLogout = () => {
    clearAuthToken();
    setFarmer(null);
    setView('home');
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      <Navbar
        currentLang={currentLang}
        onLanguageChange={setCurrentLang}
        translations={translationsMap[currentLang] || translationsMap.en}
        farmer={farmer}
        onLogout={handleLogout}
        onOpenAuth={() => setIsAuthOpen(true)}
      />

      <div className="flex-1">
        {view === 'home' && (
          <Home
            translations={translationsMap[currentLang] || translationsMap.en}
            farmer={farmer}
            onOpenAuth={() => setIsAuthOpen(true)}
            onOpenDashboard={() => setView('dashboard')}
          />
        )}

        {view === 'dashboard' && farmer && (
          <Dashboard
            farmer={farmer}
            onFarmerUpdated={(f) => setFarmer(f)}
            onLogout={handleLogout}
            t={t}
            lang={currentLang}
          />
        )}

        {view === 'wizard' && farmer && (
          <FarmSetupWizard
            onFarmCreated={() => {
              // Refresh farmer status
              api.getMe().then((f) => {
                setFarmer(f);
                setView('dashboard');
              });
            }}
            onCancel={() => setView(farmer.has_farms ? 'dashboard' : 'home')}
            t={t}
            lang={currentLang}
          />
        )}
      </div>

      <AuthModal
        isOpen={isAuthOpen}
        onClose={() => setIsAuthOpen(false)}
        onSuccess={handleLoginSuccess}
        t={t}
      />
    </div>
  );
}
