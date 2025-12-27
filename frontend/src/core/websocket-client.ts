/**
 * WebSocket client for real-time voice chat communication
 * Framework-agnostic implementation
 */

export type ConnectionState = "disconnected" | "connecting" | "connected";

export interface WebSocketClientOptions {
  url: string;
  onStateChange: (state: ConnectionState) => void;
  onMessage?: (data: unknown) => void;
  onError?: (error: Event) => void;
}

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private options: WebSocketClientOptions;

  constructor(options: WebSocketClientOptions) {
    this.options = options;
  }

  /**
   * Get current connection state
   */
  getState(): ConnectionState {
    if (!this.ws) return "disconnected";
    switch (this.ws.readyState) {
      case WebSocket.CONNECTING:
        return "connecting";
      case WebSocket.OPEN:
        return "connected";
      default:
        return "disconnected";
    }
  }

  /**
   * Establish WebSocket connection
   */
  connect(): void {
    // Prevent duplicate connections
    if (this.ws?.readyState === WebSocket.OPEN) {
      return;
    }

    // Clean up existing connection if any
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this.options.onStateChange("connecting");

    try {
      this.ws = new WebSocket(this.options.url);

      this.ws.onopen = () => {
        this.options.onStateChange("connected");
      };

      this.ws.onclose = () => {
        this.options.onStateChange("disconnected");
        this.ws = null;
      };

      this.ws.onerror = (event) => {
        this.options.onError?.(event);
        // Note: onclose will also fire after onerror, so we don't set ws=null here
        // to avoid race conditions. onclose handler will clean up.
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.options.onMessage?.(data);
        } catch {
          // If not JSON, pass raw data
          this.options.onMessage?.(event.data);
        }
      };
    } catch {
      this.options.onStateChange("disconnected");
    }
  }

  /**
   * Close WebSocket connection
   */
  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.options.onStateChange("disconnected");
  }

  /**
   * Send data through WebSocket
   * Supports string, ArrayBuffer, or objects (JSON serialized)
   */
  send(data: string | ArrayBuffer | object): boolean {
    if (this.ws?.readyState === WebSocket.OPEN) {
      if (typeof data === "string" || data instanceof ArrayBuffer) {
        this.ws.send(data);
      } else {
        this.ws.send(JSON.stringify(data));
      }
      return true;
    }
    return false;
  }

  /**
   * Check if connection is open
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}
