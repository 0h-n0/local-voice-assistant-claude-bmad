/**
 * WebSocket event types for Voice Assistant
 * Client → Server events for VAD (Voice Activity Detection)
 */

/** Event sent when speech is detected */
export interface VadStartEvent {
  type: "vad.start";
  timestamp: number;
}

/** Event sent with audio data during speech */
export interface VadAudioEvent {
  type: "vad.audio";
  audio: ArrayBuffer;
  sampleRate: 16000;
}

/** Event sent when speech ends */
export interface VadEndEvent {
  type: "vad.end";
  timestamp: number;
}

/** Cancel ongoing processing */
export interface CancelEvent {
  type: "cancel";
}

/** Union of all client-to-server events */
export type ClientEvent = VadStartEvent | VadAudioEvent | VadEndEvent | CancelEvent;

// ============================================
// Server → Client Events
// ============================================

/** Partial STT recognition result (streaming, optional) */
export interface SttPartialEvent {
  type: "stt.partial";
  text: string;
}

/** Final STT recognition result */
export interface SttFinalEvent {
  type: "stt.final";
  text: string;
  latency_ms: number;
}

/** Error event from server */
export interface ErrorEvent {
  type: "error";
  code: string;
  message: string;
}

// ============================================
// LLM Events (Story 2.4)
// ============================================

/** LLM processing started */
export interface LlmStartEvent {
  type: "llm.start";
}

/** LLM streaming token */
export interface LlmDeltaEvent {
  type: "llm.delta";
  text: string;
}

/** LLM processing completed */
export interface LlmEndEvent {
  type: "llm.end";
  latency_ms: number;
  ttft_ms: number;
}

// ============================================
// TTS Events (Story 2.5)
// ============================================

/** TTS audio chunk */
export interface TtsChunkEvent {
  type: "tts.chunk";
  audio: string; // base64 encoded PCM16 audio
  sampleRate: number;
  format: "pcm16";
}

/** TTS processing completed */
export interface TtsEndEvent {
  type: "tts.end";
  latency_ms: number;
}

/** Union of all server-to-client events */
export type ServerEvent =
  | SttPartialEvent
  | SttFinalEvent
  | LlmStartEvent
  | LlmDeltaEvent
  | LlmEndEvent
  | TtsChunkEvent
  | TtsEndEvent
  | ErrorEvent;

/** Recording state for UI */
export type RecordingState = "idle" | "recording" | "processing";

/**
 * Parse incoming server event from JSON
 */
export function parseServerEvent(data: unknown): ServerEvent | null {
  if (typeof data !== "object" || data === null) {
    return null;
  }
  const event = data as Record<string, unknown>;
  const type = event.type;

  if (type === "stt.partial" && typeof event.text === "string") {
    return { type: "stt.partial", text: event.text };
  }

  if (
    type === "stt.final" &&
    typeof event.text === "string" &&
    typeof event.latency_ms === "number"
  ) {
    return {
      type: "stt.final",
      text: event.text,
      latency_ms: event.latency_ms,
    };
  }

  if (
    type === "error" &&
    typeof event.code === "string" &&
    typeof event.message === "string"
  ) {
    return { type: "error", code: event.code, message: event.message };
  }

  // LLM events (Story 2.4)
  if (type === "llm.start") {
    return { type: "llm.start" };
  }

  if (type === "llm.delta" && typeof event.text === "string") {
    return { type: "llm.delta", text: event.text };
  }

  if (
    type === "llm.end" &&
    typeof event.latency_ms === "number" &&
    typeof event.ttft_ms === "number"
  ) {
    return {
      type: "llm.end",
      latency_ms: event.latency_ms,
      ttft_ms: event.ttft_ms,
    };
  }

  // TTS events (Story 2.5)
  if (
    type === "tts.chunk" &&
    typeof event.audio === "string" &&
    typeof event.sampleRate === "number" &&
    event.format === "pcm16"
  ) {
    return {
      type: "tts.chunk",
      audio: event.audio,
      sampleRate: event.sampleRate,
      format: "pcm16",
    };
  }

  if (type === "tts.end" && typeof event.latency_ms === "number") {
    return {
      type: "tts.end",
      latency_ms: event.latency_ms,
    };
  }

  return null;
}

/**
 * Send a typed event through WebSocket
 * Handles ArrayBuffer serialization for audio data
 */
export function serializeEvent(
  event: ClientEvent
): string | ArrayBuffer {
  if (event.type === "vad.audio") {
    // Binary protocol: [4-byte header length (little-endian)] [JSON header] [audio data]
    // Must match backend's int.from_bytes(data[:4], byteorder="little")
    const headerJson = JSON.stringify({ type: event.type, sampleRate: event.sampleRate });
    const headerBytes = new TextEncoder().encode(headerJson);

    const combined = new Uint8Array(4 + headerBytes.length + event.audio.byteLength);

    // Write header length as little-endian uint32
    const headerLengthView = new DataView(combined.buffer, 0, 4);
    headerLengthView.setUint32(0, headerBytes.length, true); // true = little-endian

    // Write header and audio data
    combined.set(headerBytes, 4);
    combined.set(new Uint8Array(event.audio), 4 + headerBytes.length);

    return combined.buffer;
  }
  return JSON.stringify(event);
}
