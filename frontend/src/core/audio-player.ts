/**
 * Audio player for TTS playback using Web Audio API
 * Story 2.5: TTS Integration
 */

export class AudioPlayer {
  private audioContext: AudioContext | null = null;
  private audioQueue: AudioBuffer[] = [];
  private isPlaying = false;
  private currentSource: AudioBufferSourceNode | null = null;
  private hasResumed = false;
  private onPlaybackCompleteCallback: (() => void) | null = null;

  /**
   * Get or create the AudioContext (lazy initialization)
   */
  private getAudioContext(): AudioContext {
    if (!this.audioContext) {
      this.audioContext = new AudioContext({ sampleRate: 44100 });
    }
    return this.audioContext;
  }

  /**
   * Decode base64 PCM16 audio data to AudioBuffer
   * @throws Error if base64 decoding or buffer creation fails
   */
  async decodeBase64Audio(
    base64: string,
    sampleRate: number
  ): Promise<AudioBuffer> {
    const ctx = this.getAudioContext();

    // Decode base64 to binary with error handling
    let binaryString: string;
    try {
      binaryString = atob(base64);
    } catch {
      throw new Error("Invalid base64 audio data");
    }

    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }

    // PCM16 to Float32 conversion
    const int16Array = new Int16Array(bytes.buffer);
    const float32Array = new Float32Array(int16Array.length);
    for (let i = 0; i < int16Array.length; i++) {
      float32Array[i] = int16Array[i] / 32768;
    }

    // Create AudioBuffer
    const audioBuffer = ctx.createBuffer(1, float32Array.length, sampleRate);
    audioBuffer.copyToChannel(float32Array, 0);

    return audioBuffer;
  }

  /**
   * Add audio chunk to queue and start playback if not already playing
   */
  async enqueue(base64Audio: string, sampleRate: number): Promise<void> {
    const buffer = await this.decodeBase64Audio(base64Audio, sampleRate);
    this.audioQueue.push(buffer);

    if (!this.isPlaying) {
      this.playNext();
    }
  }

  /**
   * Play the next audio buffer in the queue
   */
  private playNext(): void {
    if (this.audioQueue.length === 0) {
      this.isPlaying = false;
      this.currentSource = null;
      // Notify that all playback is complete
      if (this.onPlaybackCompleteCallback) {
        this.onPlaybackCompleteCallback();
      }
      return;
    }

    this.isPlaying = true;
    const buffer = this.audioQueue.shift()!;
    const ctx = this.getAudioContext();

    try {
      const source = ctx.createBufferSource();
      source.buffer = buffer;
      source.connect(ctx.destination);

      this.currentSource = source;
      source.onended = () => this.playNext();
      source.start();
    } catch {
      // If this buffer fails, try the next one
      this.playNext();
    }
  }

  /**
   * Stop all audio playback and clear the queue
   */
  stop(): void {
    this.audioQueue = [];
    this.isPlaying = false;
    if (this.currentSource) {
      try {
        this.currentSource.stop();
      } catch {
        // Ignore errors if source is already stopped
      }
      this.currentSource = null;
    }
  }

  /**
   * Check if audio is currently playing
   */
  get playing(): boolean {
    return this.isPlaying;
  }

  /**
   * Get the number of audio chunks in the queue
   */
  get queueLength(): number {
    return this.audioQueue.length;
  }

  /**
   * Resume AudioContext if suspended (required for autoplay policy)
   * Only resumes once per session for efficiency.
   */
  async resume(): Promise<void> {
    if (this.hasResumed) {
      return;
    }
    const ctx = this.getAudioContext();
    if (ctx.state === "suspended") {
      await ctx.resume();
    }
    this.hasResumed = true;
  }

  /**
   * Set callback to be called when all queued audio finishes playing
   */
  onPlaybackComplete(callback: (() => void) | null): void {
    this.onPlaybackCompleteCallback = callback;
  }
}

// Singleton instance for global access
let audioPlayerInstance: AudioPlayer | null = null;

export function getAudioPlayer(): AudioPlayer {
  if (!audioPlayerInstance) {
    audioPlayerInstance = new AudioPlayer();
  }
  return audioPlayerInstance;
}
