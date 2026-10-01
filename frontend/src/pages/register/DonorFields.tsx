import type { DonorType } from "../../types/auth";

const DONOR_TYPES: DonorType[] = ["restaurant", "event", "individual"];

interface DonorFieldsProps {
  businessName: string;
  onBusinessNameChange: (value: string) => void;
  donorType: DonorType;
  onDonorTypeChange: (value: DonorType) => void;
  address: string;
  onAddressChange: (value: string) => void;
}

export default function DonorFields({
  businessName,
  onBusinessNameChange,
  donorType,
  onDonorTypeChange,
  address,
  onAddressChange,
}: DonorFieldsProps) {
  return (
    <>
      <label className="field">
        <span className="label">Business name (optional)</span>
        <input
          type="text"
          value={businessName}
          onChange={(e) => onBusinessNameChange(e.target.value)}
          className="input"
        />
      </label>

      <label className="field">
        <span className="label">Donor type</span>
        <select
          value={donorType}
          onChange={(e) => onDonorTypeChange(e.target.value as DonorType)}
          className="input"
        >
          {DONOR_TYPES.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
      </label>

      <label className="field">
        <span className="label">Address (optional)</span>
        <input
          type="text"
          value={address}
          onChange={(e) => onAddressChange(e.target.value)}
          className="input"
        />
      </label>
    </>
  );
}
