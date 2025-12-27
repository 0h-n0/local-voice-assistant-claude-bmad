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

/** Recording state for UI */
export type RecordingState = "idle" | "recording" | "processing";

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
