import React, { useEffect, useState } from "react";
import { GpsButton } from "../components/GpsButton";
import { api, CatalogCrop, FarmRecord } from "../services/api";

interface FarmSetupWizardProps {
  onFarmCreated: (farm: FarmRecord) => void;
  onCancel: () => void;
  t: (key: string) => string;
  lang: string;
}

export const FarmSetupWizard: React.FC<FarmSetupWizardProps> = ({
  onFarmCreated,
  onCancel,
  t,
  lang,
}) => {
  const [step, setStep] = useState<1 | 2>(1);
  const [createdFarmId, setCreatedFarmId] = useState<number | null>(null);

  // Step 1: Farm Infrastructure
  const [name, setName] = useState("");
  const [latitude, setLatitude] = useState<string>("12.9716");
  const [longitude, setLongitude] = useState<string>("77.5946");
  const [areaAcres, setAreaAcres] = useState<string>("2.5");
  const [soilType, setSoilType] = useState("Red Soil");
  const [waterSource, setWaterSource] = useState("Borewell");
  const [waterAvailability, setWaterAvailability] = useState("Adequate");
  const [irrigationType, setIrrigationType] = useState("Drip");
  const [pumpRate, setPumpRate] = useState<string>("");
  const [pumpProvenance, setPumpProvenance] = useState<string>("MEASURED");

  // Step 2: Crops
  const [catalog, setCatalog] = useState<CatalogCrop[]>([]);
  const [selectedCropId, setSelectedCropId] = useState<string>("");
  const [sowingDate, setSowingDate] = useState<string>(
    new Date().toISOString().split("T")[0]
  );
  const [selectedStage, setSelectedStage] = useState<string>("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load catalog on mount
  useEffect(() => {
    api
      .getCropsCatalog()
      .then((data) => {
        setCatalog(data);
        if (data.length > 0) {
          setSelectedCropId(data[0].crop_id);
          if (data[0].stages.length > 0) {
            setSelectedStage(data[0].stages[0].stage_id);
          }
        }
      })
      .catch((err) => {
        console.error("Failed to load catalog", err);
      });
  }, []);

  // Update stages when crop selection changes
  useEffect(() => {
    const crop = catalog.find((c) => c.crop_id === selectedCropId);
    if (crop && crop.stages.length > 0) {
      setSelectedStage(crop.stages[0].stage_id);
    }
  }, [selectedCropId, catalog]);

  // Handle Water Source change with auto-sync to irrigation type
  const handleWaterSourceChange = (src: string) => {
    setWaterSource(src);
    if (src === "Rainfed") {
      setIrrigationType("None (Rainfed)");
      setPumpRate("");
    } else if (irrigationType === "None (Rainfed)") {
      setIrrigationType("Drip");
    }
  };

  const handleIrrigationChange = (irr: string) => {
    setIrrigationType(irr);
    if (irr === "None (Rainfed)") {
      setWaterSource("Rainfed");
      setPumpRate("");
    }
  };

  const isRainfed =
    waterSource === "Rainfed" || irrigationType === "None (Rainfed)";

  const handleStep1Submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const lat = parseFloat(latitude);
    const lon = parseFloat(longitude);
    const acres = parseFloat(areaAcres);

    if (isNaN(lat) || isNaN(lon) || isNaN(acres) || acres <= 0) {
      setError("Please provide valid coordinates and positive area in acres.");
      return;
    }

    const dischargeRate =
      pumpRate.trim() && !isRainfed ? parseFloat(pumpRate) : null;
    const provenance =
      dischargeRate && dischargeRate > 0 ? pumpProvenance : null;

    setLoading(true);
    try {
      const farm = await api.createFarm({
        name: name.trim() || "Main Farm Parcel",
        latitude: lat,
        longitude: lon,
        area_acres: acres,
        water_source: waterSource,
        water_availability: waterAvailability,
        irrigation_type: irrigationType,
        pump_discharge_rate: dischargeRate,
        pump_rate_provenance: provenance,
        soil_type: soilType,
      });

      setCreatedFarmId(farm.id);
      setStep(2);
    } catch (err: any) {
      setError(err.message || "Failed to create farm parcel.");
    } finally {
      setLoading(false);
    }
  };

  const handleStep2Submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createdFarmId) return;
    setError(null);

    setLoading(true);
    try {
      await api.registerCrop(createdFarmId, {
        crop_id: selectedCropId,
        sowing_date: sowingDate,
        current_stage: selectedStage,
      });

      const updatedFarm = await api.getFarm(createdFarmId);
      onFarmCreated(updatedFarm);
    } catch (err: any) {
      setError(err.message || "Failed to register active crop cycle.");
    } finally {
      setLoading(false);
    }
  };

  const currentCrop = catalog.find((c) => c.crop_id === selectedCropId);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="bg-white rounded-xl shadow-2xl max-w-xl w-full p-6 my-8 border border-slate-200">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
          <div>
            <h2 className="text-xl font-bold text-slate-800">
              {t("farm_wizard_title")}
            </h2>
            <span className="text-xs font-semibold text-emerald-700">
              {step === 1 ? t("farm_wizard_step1") : t("farm_wizard_step2")}
            </span>
          </div>
          <button
            onClick={onCancel}
            className="text-slate-400 hover:text-slate-600 font-bold"
          >
            ✕
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-lg">
            {error}
          </div>
        )}

        {step === 1 ? (
          <form onSubmit={handleStep1Submit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                {t("label_farm_name")} *
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder={t("hint_farm_name")}
                required
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none"
              />
            </div>

            {/* Coordinates Dual Mode */}
            <div className="bg-slate-50 p-3.5 rounded-lg border border-slate-200 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-800">
                  {t("card_location")}
                </span>
                <GpsButton
                  onLocationFound={(lat, lon) => {
                    setLatitude(lat.toString());
                    setLongitude(lon.toString());
                  }}
                  btnText={t("btn_use_gps")}
                  successText={t("gps_success")}
                  failedText={t("gps_failed")}
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-medium text-slate-600 mb-1">
                    {t("label_latitude")} *
                  </label>
                  <input
                    type="number"
                    step="any"
                    value={latitude}
                    onChange={(e) => setLatitude(e.target.value)}
                    required
                    className="w-full px-2.5 py-1.5 text-xs bg-white border border-slate-300 rounded-md focus:ring-1 focus:ring-emerald-500"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-medium text-slate-600 mb-1">
                    {t("label_longitude")} *
                  </label>
                  <input
                    type="number"
                    step="any"
                    value={longitude}
                    onChange={(e) => setLongitude(e.target.value)}
                    required
                    className="w-full px-2.5 py-1.5 text-xs bg-white border border-slate-300 rounded-md focus:ring-1 focus:ring-emerald-500"
                  />
                </div>
              </div>
              <span className="block text-[11px] text-slate-400">
                {t("hint_gps_or_manual")}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  {t("label_area_acres")} *
                </label>
                <input
                  type="number"
                  step="0.1"
                  min="0.1"
                  value={areaAcres}
                  onChange={(e) => setAreaAcres(e.target.value)}
                  required
                  className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  {t("label_soil_type")} *
                </label>
                <select
                  value={soilType}
                  onChange={(e) => setSoilType(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                >
                  <option value="Red Soil">Red Soil (ಕೆಂಪು ಮಣ್ಣು)</option>
                  <option value="Black Soil">Black Soil (ಕಪ್ಪು ಮಣ್ಣು)</option>
                  <option value="Clay">Clay (ಜೇಡಿ ಮಣ್ಣು)</option>
                  <option value="Sandy Loam">Sandy Loam (ಮರಳು ಮಿಶ್ರಿತ)</option>
                  <option value="Alluvial">Alluvial (ಮೆಕ್ಕಲು ಮಣ್ಣು)</option>
                  <option value="Loam">Loam (ಗೋಡು ಮಣ್ಣು)</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  {t("label_water_source")} *
                </label>
                <select
                  value={waterSource}
                  onChange={(e) => handleWaterSourceChange(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                >
                  <option value="Borewell">Borewell (ಕೊಳವೆಬಾವಿ)</option>
                  <option value="Canal">Canal (ಕಾಲುವೆ)</option>
                  <option value="Rainfed">Rainfed (ಮಳೆ ಆಶ್ರಿತ)</option>
                  <option value="Farm Pond">Farm Pond (ಕೃಷಿ ಹೊಂಡ)</option>
                  <option value="Open Well / River">Open Well / River (ಬಾವಿ/ನದಿ)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  {t("label_water_availability")} *
                </label>
                <select
                  value={waterAvailability}
                  onChange={(e) => setWaterAvailability(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                >
                  <option value="Abundant">Abundant (ಧಾರಾಳ)</option>
                  <option value="Adequate">Adequate (ಸಾಕಷ್ಟು)</option>
                  <option value="Limited">Limited (ಮಿತ)</option>
                  <option value="Scarce">Scarce (ವಿರಳ)</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                {t("label_irrigation_type")} *
              </label>
              <select
                value={irrigationType}
                onChange={(e) => handleIrrigationChange(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
              >
                <option value="Drip">Drip Irrigation (ಹನಿ ನೀರಾವರಿ)</option>
                <option value="Sprinkler">Sprinkler (ತುಂತುರು ನೀರಾವರಿ)</option>
                <option value="Flood">Flood Irrigation (ಕಾಲುವೆ ಹರಿವು)</option>
                <option value="Furrow">Furrow Irrigation (ಸಾಲು ನೀರಾವರಿ)</option>
                <option value="None (Rainfed)">None (Rainfed / ಮಳೆ ಆಶ್ರಿತ)</option>
              </select>
            </div>

            {/* Pump details (Disabled for rainfed) */}
            <div className={`p-3 rounded-lg border transition-opacity ${isRainfed ? "bg-slate-100 opacity-60" : "bg-slate-50 border-slate-200"}`}>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    {t("label_pump_rate")}
                  </label>
                  <input
                    type="number"
                    step="100"
                    min="1"
                    disabled={isRainfed}
                    value={pumpRate}
                    onChange={(e) => setPumpRate(e.target.value)}
                    placeholder="e.g. 12000"
                    className="w-full px-2.5 py-1.5 text-xs bg-white border border-slate-300 rounded-md focus:ring-1 focus:ring-emerald-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    {t("label_pump_provenance")}
                  </label>
                  <select
                    disabled={isRainfed || !pumpRate.trim()}
                    value={pumpProvenance}
                    onChange={(e) => setPumpProvenance(e.target.value)}
                    className="w-full px-2.5 py-1.5 text-xs bg-white border border-slate-300 rounded-md focus:ring-1 focus:ring-emerald-500"
                  >
                    <option value="MEASURED">Measured (ಅಳೆದ ದರ)</option>
                    <option value="FARMER_ENTERED">Farmer Entered (ಅಂದಾಜು ದಾಖಲೆ)</option>
                    <option value="ESTIMATED">Estimated (ಸಾಮರ್ಥ್ಯ ಅಂದಾಜು)</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="pt-3 flex gap-3">
              <button
                type="button"
                onClick={onCancel}
                className="flex-1 px-4 py-2 text-xs font-medium text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-lg"
              >
                {t("btn_cancel")}
              </button>
              <button
                type="submit"
                disabled={loading}
                className="flex-1 px-4 py-2 text-xs font-semibold text-white bg-emerald-700 hover:bg-emerald-800 rounded-lg shadow-sm"
              >
                {loading ? "..." : t("btn_next")}
              </button>
            </div>
          </form>
        ) : (
          <form onSubmit={handleStep2Submit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                {t("label_select_crop")} *
              </label>
              <select
                value={selectedCropId}
                onChange={(e) => setSelectedCropId(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
              >
                {catalog.map((c) => (
                  <option key={c.crop_id} value={c.crop_id}>
                    {lang === "kn" ? `${c.name_kn} (${c.name_en})` : `${c.name_en} (${c.name_kn})`}
                  </option>
                ))}
              </select>
              <span className="block text-[11px] text-slate-400 mt-1">
                {t("hint_crop_catalog")}
              </span>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                {t("label_sowing_date")} *
              </label>
              <input
                type="date"
                max={new Date().toISOString().split("T")[0]}
                value={sowingDate}
                onChange={(e) => setSowingDate(e.target.value)}
                required
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                {t("label_current_stage")} *
              </label>
              <select
                value={selectedStage}
                onChange={(e) => setSelectedStage(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
              >
                {currentCrop?.stages.map((st) => (
                  <option key={st.stage_id} value={st.stage_id}>
                    {lang === "kn" ? `${st.label_kn} (${st.label_en})` : `${st.label_en} (${st.label_kn})`}
                  </option>
                ))}
              </select>
            </div>

            <div className="pt-3 flex gap-3">
              <button
                type="submit"
                disabled={loading}
                className="w-full px-4 py-2 text-xs font-semibold text-white bg-emerald-700 hover:bg-emerald-800 rounded-lg shadow-sm"
              >
                {loading ? "..." : t("btn_submit")}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
