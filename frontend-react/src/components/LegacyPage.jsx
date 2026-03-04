export function LegacyPage({ fileName }) {
  return (
    <iframe
      title={fileName}
      className="legacy-frame"
      src={`/legacy/${fileName}`}
      sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-modals allow-downloads"
    />
  );
}
