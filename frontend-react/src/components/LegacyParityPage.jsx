export function LegacyParityPage({ pageName, source }) {
  return (
    <section className="legacy-page container">
      <p className="eyebrow">Mode migration</p>
      <h1>{pageName}</h1>
      <p>
        Cette page sera migrée en React sans regression visuelle. Source actuelle:
        <code>{source}</code>
      </p>
      <div className="legacy-checklist">
        <p>Checklist de migration:</p>
        <ul>
          <li>Reprendre la meme structure visuelle</li>
          <li>Conserver classes CSS et breakpoints</li>
          <li>Comparer captures avant/apres</li>
          <li>Migrer le JavaScript vers des hooks React</li>
        </ul>
      </div>
    </section>
  );
}
