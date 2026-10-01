export type Role = "DONOR" | "NGO" | "VOLUNTEER" | "ADMIN";

export type NgoStatus = "PENDING" | "APPROVED" | "REJECTED";

export type DonorType = "restaurant" | "event" | "individual";

export type VehicleType = "none" | "bike" | "car";

export interface DonorProfile {
  business_name: string;
  donor_type: DonorType;
  address: string;
}

export interface NGOProfile {
  organization_name: string;
  registration_number: string;
  address: string;
  verification_document: string | null;
  status: NgoStatus;
  reviewed_at: string | null;
  rejection_reason: string;
}

export interface VolunteerProfile {
  vehicle_type: VehicleType;
  service_area: string;
}

export type Profile = DonorProfile | NGOProfile | VolunteerProfile | null;

export interface User {
  id: number;
  email: string;
  full_name: string;
  phone: string;
  role: Role;
  avatar: string | null;
  created_at: string;
  profile: Profile;
}

export interface LoginResponse {
  access: string;
  refresh: string;
  user: {
    id: number;
    email: string;
    full_name: string;
    role: Role;
    ngo_status: NgoStatus | null;
  };
}

export interface RegisterPayload {
  email: string;
  password: string;
  full_name?: string;
  phone?: string;
  role: Exclude<Role, "ADMIN">;

  // Donor
  business_name?: string;
  donor_type?: DonorType;
  address?: string;

  // NGO
  organization_name?: string;
  registration_number?: string;

  // Volunteer
  vehicle_type?: VehicleType;
  service_area?: string;
}
