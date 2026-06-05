import { Play } from 'lucide-react';
import { examples } from '../data/examples.js';

export default function ExampleList({ onSelect, compact = false }) {
  return (
    <div className={compact ? 'example-strip' : 'example-grid'}>
      {examples.map((example) => (
        <button className="example-card" key={example.id} onClick={() => onSelect(example)} type="button">
          <div>
            <strong>{example.title}</strong>
            <span>Expected: {example.expected}</span>
          </div>
          {!compact && <p>{example.text}</p>}
          <Play size={16} />
        </button>
      ))}
    </div>
  );
}
