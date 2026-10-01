interface NgoFieldsProps {
  organizationName: string;
  onOrganizationNameChange: (value: string) => void;
  registrationNumber: string;
  onRegistrationNumberChange: (value: string) => void;
  address: string;
  onAddressChange: (value: string) => void;
  organizationNameError?: string | null;
  registrationNumberError?: string | null;
}

export default function NgoFields({
  organizationName,
  onOrganizationNameChange,
  registrationNumber,
  onRegistrationNumberChange,
  address,
  onAddressChange,
  organizationNameError,
  registrationNumberError,
}: NgoFieldsProps) {
  return (
    <>
      <label className="field">
        <span className="label">Organization name</span>
        <input
          type="text"
          required
          value={organizationName}
          onChange={(e) => onOrganizationNameChange(e.target.value)}
          className="input"
        />
        {organizationNameError && (
          <span className="error">{organizationNameError}</span>
        )}
      </label>

      <label className="field">
        <span className="label">Registration number</span>
        <input
          type="text"
          required
          value={registrationNumber}
          onChange={(e) => onRegistrationNumberChange(e.target.value)}
          className="input"
        />
        {registrationNumberError && (
          <span className="error">{registrationNumberError}</span>
        )}
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
