export interface Case {
  id: string;
  created_at: string;
  updated_at: string;
  title: string;
  attorney_name?: string;
  client_name?: string;
  judgment_amount?: number;
  notes?: string;
  status: "open" | "active" | "closed";
}

export interface CaseCreate {
  title: string;
  attorney_name?: string;
  client_name?: string;
  judgment_amount?: number;
  notes?: string;
}

export interface Subject {
  id: string;
  case_id: string;
  created_at: string;
  full_name: string;
  country: "US" | "PK" | "BOTH";
  aliases?: string[];
  date_of_birth?: string;
  address_street?: string;
  address_city?: string;
  address_state?: string;
  address_zip?: string;
  known_employers?: string[];
  known_spouses?: string[];
  known_businesses?: string[];
  photo_url?: string | null;
}

export interface SubjectCreate {
  case_id: string;
  full_name: string;
  country?: "US" | "PK" | "BOTH";
  aliases?: string[];
  date_of_birth?: string;
  address_street?: string;
  address_city?: string;
  address_state?: string;
  address_zip?: string;
  known_employers?: string[];
  known_spouses?: string[];
  known_businesses?: string[];
}

export interface SubjectUpdate {
  full_name?: string;
  country?: "US" | "PK" | "BOTH";
  aliases?: string[];
  date_of_birth?: string;
  address_street?: string;
  address_city?: string;
  address_state?: string;
  address_zip?: string;
  known_employers?: string[];
  known_spouses?: string[];
  known_businesses?: string[];
  photo_url?: string | null;
}

export interface InvestigationJob {
  id: string;
  case_id: string;
  subject_id: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  status: "pending" | "running" | "complete" | "failed";
  error_message?: string;
}

export interface Report {
  id: string;
  case_id: string;
  job_id: string;
  created_at: string;
  court_records?: Record<string, unknown>;
  property_records?: Record<string, unknown>;
  business_filings?: Record<string, unknown>;
  social_media?: Record<string, unknown>;
  employment?: Record<string, unknown>;
  family_info?: Record<string, unknown>;
  executive_summary?: string;
  asset_summary?: string;
  risk_flags?: string[];
  full_report_md?: string;
  confidence_score?: number;
  sources_consulted?: string[];
}
