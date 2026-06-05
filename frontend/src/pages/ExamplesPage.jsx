import ExampleList from '../components/ExampleList.jsx';
import { examples } from '../data/examples.js';

export default function ExamplesPage({ onRunExample }) {
  return (
    <div className="page-stack">
      <section className="page-header">
        <span className="eyebrow">Try-ready cases</span>
        <h1>Examples</h1>
        <p>Chọn một input mẫu để đưa sang trang Demo và chạy prediction ngay.</p>
      </section>

      <section className="panel">
        <ExampleList onSelect={(example) => onRunExample(example.text)} />
      </section>

      <section className="panel examples-table">
        <h2>Expected outputs</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Use case</th>
                <th>Input</th>
                <th>Expected</th>
              </tr>
            </thead>
            <tbody>
              {examples.map((example) => (
                <tr key={example.id}>
                  <td>{example.title}</td>
                  <td>{example.text}</td>
                  <td>{example.expected}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
