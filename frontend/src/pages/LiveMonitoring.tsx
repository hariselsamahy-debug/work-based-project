import { useEffect, useState } from "react";
import { api, type Camera, type Incident } from "../api";
import { CameraTile } from "../components/CameraTile";

export function LiveMonitoring({ latest }: { latest: Incident[] }) {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [error, setError] = useState<string>();

  useEffect(() => {
    const load = () => api.cameras().then(setCameras, (e) => setError(String(e)));
    load();
    const timer = window.setInterval(load, 10_000); // refresh online status
    return () => window.clearInterval(timer);
  }, []);

  const lastAlertFor = (cameraId: string) => latest.find((i) => i.camera_id === cameraId);

  if (error) return <p className="empty">Cannot reach the backend: {error}</p>;
  if (!cameras.length) return <p className="empty">No cameras configured. Add them in backend/app/cameras.yaml.</p>;

  return (
    <section className="grid">
      {cameras.map((camera) => (
        <CameraTile key={camera.id} camera={camera} lastAlert={lastAlertFor(camera.id)} />
      ))}
    </section>
  );
}
