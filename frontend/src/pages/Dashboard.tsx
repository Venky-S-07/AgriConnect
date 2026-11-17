import React, { useEffect, useState } from "react";
import {
  api,
  CatalogCrop,
  clearAuthToken,
  CropRecord,
  FarmerProfile,
  FarmRecord,
} from "../services/api";

interface DashboardProps {
  farmer: FarmerProfile;
  onFarmerUpdated: (f: FarmerProfile) => void;
  onLogout: () => void;
  t: (key: string) => string;
  lang: string;
}

export const Dashboard: React.FC<DashboardProps> = ({
  farmer,
  onFarmerUpdated,
  onLogout,
  t,
  lang,
}) => {
  const [farms, setFarms] = useState<FarmRecord[]>([]);
  const [catalog, setCatalog] = useState<CatalogCrop[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionError, setActionError] = useState<string | null>(null);

  // Subsequent Crop Modal state
  const [activeFarmForCrop, setActiveFarmForCrop] = useState<number | null>(null);
  const [subCropId, setSubCropId] = useState("");
  const [subSowingDate, setSubSowingDate] = useState(
    new Date().toISOString().split("T")[0]
  );
  const [subStage, setSubStage] = useState("");

  // Edit Farm Modal state
  const [editingFarm, setEditingFarm] = useState<FarmRecord | null>(null);
  const [editLat, setEditLat] = useState("");
  const [editLon, setEditLon] = useState("");
  const [editName, setEditName] = useState("");

  // Update Stage Modal state
  const [stageModalCrop, setStageModalCrop] = useState<{
    farmId: number;
    crop: CropRecord;
  } | null>(null);
  const [newStage, setNewStage] = useState("");

  const refreshFarms = async () => {
    try {
      const data = await api.listFarms();
      setFarms(data);
    } catch (err: any) {
      console.error("Failed to load farms", err);
    }
  };

  useEffect(() => {
    Promise.all([api.listFarms(), api.getCropsCatalog()])
      .then(([farmsData, catalogData]) => {
        setFarms(farmsData);
        setCatalog(catalogData);
        if (catalogData.length > 0) {
          setSubCropId(catalogData[0].crop_id);
          if (catalogData[0].stages.length > 0) {
            setSubStage(catalogData[0].stages[0].stage_id);
          }
        }
      })
      .finally(() => setLoading(false));
  }, []);

  const handleWithdrawConsent = async () => {
    if (!window.confirm(t("confirm_withdraw_consent"))) return;
    try {
      const updated = await api.updateConsent({ dpdp_consent: false });
      onFarmerUpdated(updated);
    } catch (err: any) {
      setActionError(err.message);
    }
  };

  const handleReenableConsent = async () => {
    try {
      const updated = await api.updateConsent({ dpdp_consent: true });
      onFarmerUpdated(updated);
      setActionError(null);
    } catch (err: any) {
      setActionError(err.message);
    }
  };

  const handleToggleImageConsent = async (val: boolean) => {
    try {
      const updated = await api.updateConsent({ image_training_consent: val });
      onFarmerUpdated(updated);
    } catch (err: any) {
      setActionError(err.message);
    }
  };

  const handleExportData = async () => {
    try {
      const data = await api.exportData();
      const blob = new Blob([JSON.stringify(data, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `AgriConnect_Export_${farmer.phone_number}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err: any) {
      setActionError(err.message);
    }
  };

  const handleDeleteAccount = async () => {
    if (!window.confirm(t("confirm_delete_account"))) return;
    try {
      await api.deleteAccount();
      clearAuthToken();
      onLogout();
    } catch (err: any) {
      setActionError(err.message);
    }
  };

  const handleDeactivateCrop = async (farmId: number, cropRecordId: number) => {
    try {
      await api.deactivateCrop(farmId, cropRecordId);
      await refreshFarms();
    } catch (err: any) {
      setActionError(err.message);
    }
  };

  const handleRegisterSubsequentCrop = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeFarmForCrop) return;
    try {
      await api.registerCrop(activeFarmForCrop, {
        crop_id: subCropId,
        sowing_date: subSowingDate,
        current_stage: subStage,
      });
      setActiveFarmForCrop(null);
      await refreshFarms();
    } catch (err: any) {
      setActionError(err.message);
    }
  };

  const handleSaveFarmCoords = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingFarm) return;
    try {
      await api.updateFarm(editingFarm.id, {
        name: editName,
        latitude: parseFloat(editLat),
        longitude: parseFloat(editLon),
      });
      setEditingFarm(null);
      await refreshFarms();
    } catch (err: any) {
      setActionError(err.message);
    }
  };

  const handleSaveStage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!stageModalCrop) return;
    try {
      await api.updateCrop(stageModalCrop.farmId, stageModalCrop.crop.crop_record_id, {
        current_stage: newStage,
      });
      setStageModalCrop(null);
      await refreshFarms();
    } catch (err: any) {
      setActionError(err.message);
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Top Header Card */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 mb-8 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-semibold text-emerald-700 tracking-wider uppercase">
            {t("dashboard_welcome")}
          </span>
          <h1 className="text-2xl font-bold text-slate-800">
            {farmer.full_name || "Farmer"}
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            {t("dashboard_phone")}: <span className="font-medium text-slate-700">{farmer.phone_number}</span> | Preferred: {farmer.preferred_lang.toUpperCase()}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <button
            onClick={handleExportData}
            className="px-3.5 py-1.5 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 border border-slate-300 rounded-lg transition-colors flex items-center gap-1.5"
          >
            📥 {t("btn_export_data")}
          </button>
          <button
            onClick={onLogout}
            className="px-3.5 py-1.5 text-xs font-semibold text-red-700 bg-red-50 hover:bg-red-100 border border-red-200 rounded-lg transition-colors"
          >
            {t("btn_logout")}
          </button>
        </div>
      </div>

      {actionError && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl flex items-center justify-between">
          <span>{actionError}</span>
          <button onClick={() => setActionError(null)} className="font-bold">✕</button>
        </div>
      )}

      {/* Consent Warning Banner */}
      {!farmer.dpdp_consent && (
        <div className="mb-8 p-4 bg-amber-50 border border-amber-300 text-amber-900 rounded-xl text-xs leading-relaxed space-y-2">
          <div className="flex items-center gap-2 font-bold text-sm text-amber-800">
            ⚠️ {t("consent_status_withdrawn")}
          </div>
          <p>{t("consent_withdrawn_warning")}</p>
          <button
            onClick={handleReenableConsent}
            className="mt-2 px-3 py-1.5 bg-emerald-700 hover:bg-emerald-800 text-white font-semibold rounded-lg text-xs"
          >
            {t("btn_reenable_consent")}
          </button>
        </div>
      )}

      {/* Farms Section */}
      <div className="mb-10">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-slate-800">
            {t("dashboard_farms_title")} ({farms.length})
          </h2>
        </div>

        {loading ? (
          <div className="text-center py-12 text-slate-400 text-xs">Loading farm cockpit...</div>
        ) : farms.length === 0 ? (
          <div className="p-8 text-center bg-white rounded-xl border border-dashed border-slate-300 text-slate-500 text-xs">
            {t("dashboard_no_farms")}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {farms.map((farm) => {
              const activeCrop = farm.crops.find((c) => c.is_active);
              const historicalCrops = farm.crops.filter((c) => !c.is_active);
              const cropMeta = activeCrop ? catalog.find((c) => c.crop_id === activeCrop.crop_id) : null;

              return (
                <div
                  key={farm.id}
                  className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden flex flex-col justify-between"
                >
                  <div className="p-5">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h3 className="text-base font-bold text-slate-800">{farm.name}</h3>
                        <span className="text-xs text-slate-500">
                          {farm.area_acres} Acres • {farm.soil_type}
                        </span>
                      </div>
                      <button
                        onClick={() => {
                          setEditingFarm(farm);
                          setEditName(farm.name);
                          setEditLat(farm.latitude.toString());
                          setEditLon(farm.longitude.toString());
                        }}
                        className="text-xs font-semibold text-emerald-700 hover:underline"
                      >
                        {t("btn_edit_farm")}
                      </button>
                    </div>

                    {/* Infrastructure Grid */}
                    <div className="grid grid-cols-2 gap-2 text-[11px] bg-slate-50 p-3 rounded-lg border border-slate-100 mb-4">
                      <div>
                        <span className="text-slate-400">{t("card_water")}: </span>
                        <strong className="text-slate-700">{farm.water_source} ({farm.water_availability})</strong>
                      </div>
                      <div>
                        <span className="text-slate-400">{t("card_irrigation")}: </span>
                        <strong className="text-slate-700">{farm.irrigation_type}</strong>
                      </div>
                      <div>
                        <span className="text-slate-400">{t("card_pump")}: </span>
                        <strong className="text-slate-700">
                          {farm.pump_discharge_rate ? `${farm.pump_discharge_rate} L/h (${farm.pump_rate_provenance})` : "N/A"}
                        </strong>
                      </div>
                      <div>
                        <span className="text-slate-400">{t("card_location")}: </span>
                        <strong className="text-slate-700">{farm.latitude.toFixed(4)}, {farm.longitude.toFixed(4)}</strong>
                      </div>
                    </div>

                    {/* Active Crop Card */}
                    <div className="border-t border-slate-100 pt-3">
                      <span className="text-xs font-semibold text-slate-800 block mb-2">
                        {t("dashboard_active_crop")}
                      </span>
                      {activeCrop ? (
                        <div className="p-3 bg-emerald-50/70 border border-emerald-200 rounded-lg">
                          <div className="flex items-center justify-between mb-1.5">
                            <span className="text-sm font-bold text-emerald-900">
                              {cropMeta ? (lang === "kn" ? cropMeta.name_kn : cropMeta.name_en) : activeCrop.crop_id}
                            </span>
                            <span className="px-2 py-0.5 text-[10px] font-semibold bg-emerald-700 text-white rounded-full">
                              {activeCrop.current_stage}
                            </span>
                          </div>
                          <p className="text-[11px] text-emerald-800">
                            {t("label_sowing_date")}: <strong>{activeCrop.sowing_date}</strong>
                          </p>

                          <div className="mt-3 flex gap-2">
                            <button
                              onClick={() => {
                                setStageModalCrop({ farmId: farm.id, crop: activeCrop });
                                setNewStage(activeCrop.current_stage);
                              }}
                              className="px-2.5 py-1 text-xs font-semibold bg-white text-emerald-800 border border-emerald-300 rounded hover:bg-emerald-100"
                            >
                              {t("btn_update_stage")}
                            </button>
                            <button
                              onClick={() => handleDeactivateCrop(farm.id, activeCrop.crop_record_id)}
                              className="px-2.5 py-1 text-xs font-medium bg-white text-slate-700 border border-slate-300 rounded hover:bg-slate-100"
                            >
                              {t("btn_deactivate_crop")}
                            </button>
                          </div>
                        </div>
                      ) : (
                        <div className="p-3 bg-slate-50 border border-dashed border-slate-200 rounded-lg text-center">
                          <p className="text-xs text-slate-500 mb-2">{t("dashboard_no_active_crop")}</p>
                          <button
                            onClick={() => {
                              setActiveFarmForCrop(farm.id);
                              if (catalog.length > 0) {
                                setSubCropId(catalog[0].crop_id);
                                setSubStage(catalog[0].stages[0]?.stage_id || "SOWING");
                              }
                            }}
                            className="px-3 py-1.5 text-xs font-semibold bg-emerald-700 text-white rounded hover:bg-emerald-800"
                          >
                            + {t("btn_add_crop")}
                          </button>
                        </div>
                      )}
                    </div>

                    {/* Historical Crops */}
                    {historicalCrops.length > 0 && (
                      <div className="mt-4 pt-3 border-t border-slate-100">
                        <span className="text-[11px] font-semibold text-slate-400 block mb-1.5">
                          {t("dashboard_historical_crops")} ({historicalCrops.length})
                        </span>
                        <div className="space-y-1">
                          {historicalCrops.map((hc) => (
                            <div key={hc.crop_record_id} className="text-xs text-slate-500 flex justify-between">
                              <span>{hc.crop_id.toUpperCase()} (Sown: {hc.sowing_date})</span>
                              <span className="text-slate-400">{hc.current_stage}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Consent & Privacy Management Section */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 mb-8">
        <h2 className="text-base font-bold text-slate-800 mb-4">
          {t("consent_panel_title")}
        </h2>

        <div className="space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div>
              <span className="text-xs font-semibold text-slate-800 block">
                {farmer.dpdp_consent ? t("consent_status_active") : t("consent_status_withdrawn")}
              </span>
              <span className="text-[11px] text-slate-500">
                Policy: {farmer.dpdp_policy_version} • Consented: {new Date(farmer.dpdp_consent_time).toLocaleDateString()}
              </span>
            </div>
            {farmer.dpdp_consent ? (
              <button
                onClick={handleWithdrawConsent}
                className="px-3 py-1 text-xs font-semibold text-amber-800 bg-amber-50 hover:bg-amber-100 border border-amber-300 rounded-md"
              >
                {t("btn_withdraw_consent")}
              </button>
            ) : (
              <button
                onClick={handleReenableConsent}
                className="px-3 py-1 text-xs font-semibold text-emerald-800 bg-emerald-50 hover:bg-emerald-100 border border-emerald-300 rounded-md"
              >
                {t("btn_reenable_consent")}
              </button>
            )}
          </div>

          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div>
              <span className="text-xs font-semibold text-slate-800 block">
                {t("toggle_image_consent")}
              </span>
              <span className="text-[11px] text-slate-500">
                Status: {farmer.image_training_consent ? "Granted" : "Withdrawn / Inactive"}
              </span>
            </div>
            <input
              type="checkbox"
              checked={farmer.image_training_consent}
              onChange={(e) => handleToggleImageConsent(e.target.checked)}
              className="h-4 w-4 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
            />
          </div>

          <div className="flex items-center justify-between pt-2">
            <div>
              <span className="text-xs font-semibold text-red-700 block">
                Permanent Data Deletion
              </span>
              <span className="text-[11px] text-slate-400">
                Purges account, farms, crops, and consent records permanently.
              </span>
            </div>
            <button
              onClick={handleDeleteAccount}
              className="px-3 py-1.5 text-xs font-semibold text-white bg-red-700 hover:bg-red-800 rounded-lg"
            >
              {t("btn_delete_account")}
            </button>
          </div>
        </div>
      </div>

      {/* Subsequent Crop Modal */}
      {activeFarmForCrop && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
            <h3 className="text-base font-bold text-slate-800 mb-4">{t("btn_add_crop")}</h3>
            <form onSubmit={handleRegisterSubsequentCrop} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">{t("label_select_crop")}</label>
                <select
                  value={subCropId}
                  onChange={(e) => setSubCropId(e.target.value)}
                  className="w-full px-3 py-2 text-sm border rounded-lg"
                >
                  {catalog.map((c) => (
                    <option key={c.crop_id} value={c.crop_id}>
                      {lang === "kn" ? c.name_kn : c.name_en}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">{t("label_sowing_date")}</label>
                <input
                  type="date"
                  max={new Date().toISOString().split("T")[0]}
                  value={subSowingDate}
                  onChange={(e) => setSubSowingDate(e.target.value)}
                  className="w-full px-3 py-2 text-sm border rounded-lg"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">{t("label_current_stage")}</label>
                <select
                  value={subStage}
                  onChange={(e) => setSubStage(e.target.value)}
                  className="w-full px-3 py-2 text-sm border rounded-lg"
                >
                  {catalog
                    .find((c) => c.crop_id === subCropId)
                    ?.stages.map((st) => (
                      <option key={st.stage_id} value={st.stage_id}>
                        {lang === "kn" ? st.label_kn : st.label_en}
                      </option>
                    ))}
                </select>
              </div>

              <div className="flex gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setActiveFarmForCrop(null)}
                  className="flex-1 px-3 py-2 text-xs bg-slate-100 rounded-lg"
                >
                  {t("btn_cancel")}
                </button>
                <button
                  type="submit"
                  className="flex-1 px-3 py-2 text-xs font-semibold bg-emerald-700 text-white rounded-lg"
                >
                  {t("btn_submit")}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Farm Modal */}
      {editingFarm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
            <h3 className="text-base font-bold text-slate-800 mb-4">{t("btn_edit_farm")}</h3>
            <form onSubmit={handleSaveFarmCoords} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">{t("label_farm_name")}</label>
                <input
                  type="text"
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  className="w-full px-3 py-2 text-sm border rounded-lg"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">{t("label_latitude")}</label>
                  <input
                    type="number"
                    step="any"
                    value={editLat}
                    onChange={(e) => setEditLat(e.target.value)}
                    className="w-full px-3 py-2 text-sm border rounded-lg"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">{t("label_longitude")}</label>
                  <input
                    type="number"
                    step="any"
                    value={editLon}
                    onChange={(e) => setEditLon(e.target.value)}
                    className="w-full px-3 py-2 text-sm border rounded-lg"
                    required
                  />
                </div>
              </div>

              <div className="flex gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setEditingFarm(null)}
                  className="flex-1 px-3 py-2 text-xs bg-slate-100 rounded-lg"
                >
                  {t("btn_cancel")}
                </button>
                <button
                  type="submit"
                  className="flex-1 px-3 py-2 text-xs font-semibold bg-emerald-700 text-white rounded-lg"
                >
                  {t("btn_save")}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Update Stage Modal */}
      {stageModalCrop && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-sm w-full p-6">
            <h3 className="text-base font-bold text-slate-800 mb-4">{t("btn_update_stage")}</h3>
            <form onSubmit={handleSaveStage} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">{t("label_current_stage")}</label>
                <select
                  value={newStage}
                  onChange={(e) => setNewStage(e.target.value)}
                  className="w-full px-3 py-2 text-sm border rounded-lg"
                >
                  {catalog
                    .find((c) => c.crop_id === stageModalCrop.crop.crop_id)
                    ?.stages.map((st) => (
                      <option key={st.stage_id} value={st.stage_id}>
                        {lang === "kn" ? st.label_kn : st.label_en}
                      </option>
                    ))}
                </select>
              </div>

              <div className="flex gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setStageModalCrop(null)}
                  className="flex-1 px-3 py-2 text-xs bg-slate-100 rounded-lg"
                >
                  {t("btn_cancel")}
                </button>
                <button
                  type="submit"
                  className="flex-1 px-3 py-2 text-xs font-semibold bg-emerald-700 text-white rounded-lg"
                >
                  {t("btn_save")}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
