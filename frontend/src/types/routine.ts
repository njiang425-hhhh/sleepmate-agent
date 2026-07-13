export interface RoutineStep {
  order: number;
  action: string;
  duration_seconds: number;
  instruction: string;
}

export interface SleepRoutine {
  title: string;
  duration_minutes: number;
  strategy: string;
  steps: RoutineStep[];
  script: string;
}

export interface SafetyResource {
  name: string;
  phone?: string;
  url?: string;
}

export interface RoutineMeta {
  history_available: boolean;
  history_record_count: number;
  generation_mode: "mock" | "real" | "fallback" | "rule_based";
  generated_at: string;
}

export interface RoutineSuccessResponse {
  type: "success";
  routine: SleepRoutine;
  safety_notice: string;
  meta: RoutineMeta;
}

export interface SupportiveClarificationResponse {
  type: "supportive_clarification";
  message: string;
  resources: SafetyResource[];
  meta: RoutineMeta;
}

export interface SafetyRedirectResponse {
  type: "safety_redirect";
  message: string;
  resources: SafetyResource[];
  immediate_actions: string[];
  meta: RoutineMeta;
}

export type RoutineGenerateResponse =
  | RoutineSuccessResponse
  | SupportiveClarificationResponse
  | SafetyRedirectResponse;
