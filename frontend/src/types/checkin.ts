export interface CheckinData {
  mood: string;
  energy_level: number;
  stress_level: number;
  caffeine_after_3pm: boolean;
  screen_time_minutes: number;
  available_minutes: number;
  preferred_audio: string;
  notes?: string;
}

export interface Analysis {
  sleep_risk_level: string;
  suggestions: string[];
  recommended_activity: string;
  recommended_duration_minutes: number;
}

export interface CheckinResponse {
  status: string;
  checkin: CheckinData;
  analysis: Analysis;
}
