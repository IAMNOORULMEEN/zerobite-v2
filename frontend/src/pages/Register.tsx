import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";
import type {
  DonorType,
  RegisterPayload,
  Role,
  VehicleType,
} from "../types/auth";
import DonorFields from "./register/DonorFields";
import NgoFields from "./register/NgoFields";
import VolunteerFields from "./register/VolunteerFields";
import styles from "./Register.module.scss";

const ROLES: Exclude<Role, "ADMIN">[] = ["DONOR", "NGO", "VOLUNTEER"];

interface FieldErrors {
  [key: string]: string | string[] | undefined;
}

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("");
  const [role, setRole] = useState<Exclude<Role, "ADMIN">>("DONOR");

  // Donor
  const [businessName, setBusinessName] = useState("");
  const [donorType, setDonorType] = useState<DonorType>("individual");
  const [address, setAddress] = useState("");

  // NGO
  const [organizationName, setOrganizationName] = useState("");
  const [registrationNumber, setRegistrationNumber] = useState("");

  // Volunteer
  const [vehicleType, setVehicleType] = useState<VehicleType>("none");
  const [serviceArea, setServiceArea] = useState("");

  const [errors, setErrors] = useState<FieldErrors>({});
  const [generalError, setGeneralError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  function fieldError(name: string): string | null {
    const value = errors[name];
    if (!value) return null;
    return Array.isArray(value) ? value.join(" ") : value;
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrors({});
    setGeneralError(null);
    setSubmitting(true);

    const payload: RegisterPayload = {
      email: email.trim(),
      password,
      full_name: fullName.trim() || undefined,
      phone: phone.trim() || undefined,
      role,
    };

    if (role === "DONOR") {
      if (businessName) payload.business_name = businessName.trim();
      payload.donor_type = donorType;
      if (address) payload.address = address.trim();
    } else if (role === "NGO") {
      payload.organization_name = organizationName.trim();
      payload.registration_number = registrationNumber.trim();
      if (address) payload.address = address.trim();
    } else if (role === "VOLUNTEER") {
      payload.vehicle_type = vehicleType;
      if (serviceArea) payload.service_area = serviceArea.trim();
    }

    try {
      await register(payload);
      navigate("/login", { replace: true });
    } catch (err) {
      const data = (err as { response?: { data?: unknown } })?.response?.data;
      if (data && typeof data === "object") {
        setErrors(data as FieldErrors);
        const detail = (data as { detail?: unknown }).detail;
        if (typeof detail === "string") {
          setGeneralError(detail);
        }
      } else {
        setGeneralError("Registration failed. Please try again.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className={styles.wrap}>
      <h1 className={styles.title}>Create an account</h1>

      <form className={styles.form} onSubmit={onSubmit} noValidate>
        <label className={styles.field}>
          <span className={styles.label}>Email</span>
          <input
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className={styles.input}
          />
          {fieldError("email") && (
            <span className={styles.error}>{fieldError("email")}</span>
          )}
        </label>

        <label className={styles.field}>
          <span className={styles.label}>Password</span>
          <input
            type="password"
            autoComplete="new-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className={styles.input}
          />
          {fieldError("password") && (
            <span className={styles.error}>{fieldError("password")}</span>
          )}
        </label>

        <label className={styles.field}>
          <span className={styles.label}>Full name</span>
          <input
            type="text"
            autoComplete="name"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            className={styles.input}
          />
        </label>

        <label className={styles.field}>
          <span className={styles.label}>Phone</span>
          <input
            type="tel"
            autoComplete="tel"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            className={styles.input}
          />
        </label>

        <fieldset className={styles.roleGroup}>
          <legend className={styles.label}>I am a…</legend>
          {ROLES.map((r) => (
            <label key={r} className={styles.radio}>
              <input
                type="radio"
                name="role"
                value={r}
                checked={role === r}
                onChange={() => setRole(r)}
              />
              <span>{r.charAt(0) + r.slice(1).toLowerCase()}</span>
            </label>
          ))}
        </fieldset>

        {role === "DONOR" && (
          <DonorFields
            businessName={businessName}
            onBusinessNameChange={setBusinessName}
            donorType={donorType}
            onDonorTypeChange={setDonorType}
            address={address}
            onAddressChange={setAddress}
          />
        )}

        {role === "NGO" && (
          <NgoFields
            organizationName={organizationName}
            onOrganizationNameChange={setOrganizationName}
            registrationNumber={registrationNumber}
            onRegistrationNumberChange={setRegistrationNumber}
            address={address}
            onAddressChange={setAddress}
            organizationNameError={fieldError("organization_name")}
            registrationNumberError={fieldError("registration_number")}
          />
        )}

        {role === "VOLUNTEER" && (
          <VolunteerFields
            vehicleType={vehicleType}
            onVehicleTypeChange={setVehicleType}
            serviceArea={serviceArea}
            onServiceAreaChange={setServiceArea}
          />
        )}

        {generalError && (
          <p className={styles.error} role="alert">
            {generalError}
          </p>
        )}

        <button type="submit" className={styles.submit} disabled={submitting}>
          {submitting ? "Creating account…" : "Create account"}
        </button>
      </form>

      <p className={styles.aside}>
        Already have an account? <Link to="/login">Sign in</Link>
      </p>
    </section>
  );
}
