import { useEffect, useRef } from "react";
import type { Incident } from "./api";

/** Calls onIncident for every alert the backend pushes; reconnects if the socket drops. */
export function useAlertsSocket(onIncident: (incident: Incident) => void) {
  const handler = useRef(onIncident);
  handler.current = onIncident;

  useEffect(() => {
    let socket: WebSocket | null = null;
    let retry: number | undefined;
    let closed = false;

    const connect = () => {
      const protocol = location.protocol === "https:" ? "wss" : "ws";
      socket = new WebSocket(`${protocol}://${location.host}/ws/alerts`);
      socket.onmessage = (event) => {
        const message = JSON.parse(event.data);
        if (message.event === "incident") handler.current(message.incident);
      };
      socket.onclose = () => {
        if (!closed) retry = window.setTimeout(connect, 3000);
      };
    };
    connect();

    return () => {
      closed = true;
      window.clearTimeout(retry);
      socket?.close();
    };
  }, []);
}
