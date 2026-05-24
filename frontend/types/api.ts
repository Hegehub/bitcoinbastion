export type ApiError = { code: string; message: string; request_id?: string }
export type ApiEnvelope<T> = { success?: boolean; data?: T; error?: ApiError; meta?: { version?: string } }

export type PublicStatusDTO = { platform_status: string; production_calibrated: boolean; known_limitations: string[] }
export type RuntimeEventDTO = { event_type: string; severity: string; status?: string; message?: string }
