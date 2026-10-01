import type { VehicleType } from "../../types/auth";

const VEHICLE_TYPES: VehicleType[] = ["none", "bike", "car"];

interface VolunteerFieldsProps {
  vehicleType: VehicleType;
  onVehicleTypeChange: (value: VehicleType) => void;
  serviceArea: string;
  onServiceAreaChange: (value: string) => void;
}

export default function VolunteerFields({
  vehicleType,
  onVehicleTypeChange,
  serviceArea,
  onServiceAreaChange,
}: VolunteerFieldsProps) {
  return (
    <>
      <label className="field">
        <span className="label">Vehicle type</span>
        <select
          value={vehicleType}
          onChange={(e) => onVehicleTypeChange(e.target.value as VehicleType)}
          className="input"
        >
          {VEHICLE_TYPES.map((v) => (
            <option key={v} value={v}>
              {v}
            </option>
          ))}
        </select>
      </label>

      <label className="field">
        <span className="label">Service area (optional)</span>
        <input
          type="text"
          value={serviceArea}
          onChange={(e) => onServiceAreaChange(e.target.value)}
          className="input"
        />
      </label>
    </>
  );
}
