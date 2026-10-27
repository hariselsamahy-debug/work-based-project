import { api, type Camera, type Incident, violationLabel } from "../api";

interface Props {
  camera: Camera;
  lastAlert?: Incident;
}

export function CameraTile({ camera, lastAlert }: Props) {
  const recent = lastAlert && Date.now() - new Date(lastAlert.created_at).getTime() < 15_000;

  return (
    <article className={`tile ${recent ? "tile-alert" : ""}`}>
      <div className="tile-video">
        {camera.online ? (
          <img src={api.streamUrl(camera.id)} alt={`Live view of ${camera.name}`} />
        ) : (
          <div className="tile-offline">Camera offline</div>
        )}
      </div>
      <footer className="tile-footer">
        <div>
          <div className="tile-name">
            <span className={`dot ${camera.online ? "dot-on" : "dot-off"}`} />
            {camera.name}
          </div>
          <div className="muted">{camera.zone}</div>
        </div>
        {lastAlert && (
          <div className="tile-last">
            <div>{violationLabel(lastAlert.type)}</div>
            <div className="muted">{new Date(lastAlert.created_at).toLocaleTimeString()}</div>
          </div>
        )}
      </footer>
    </article>
  );
}
