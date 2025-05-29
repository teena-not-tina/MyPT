import React, { useState } from 'react';
import { analyzeImage } from '../../services/api';

const MainPage = () => {
  const [image, setImage] = useState(null);
  const [results, setResults] = useState(null);

  const handleChange = (e) => {
    setImage(e.target.files[0]);
  };

  const handleSubmit = async () => {
    if (!image) return;
    const result = await analyzeImage(image);
    setResults(result);
  };

  return (
    <div className="p-4">
      <input type="file" onChange={handleChange} />
      <button onClick={handleSubmit}>분석</button>

      {results && (
        <div className="mt-4">
          <h3>탐지 결과:</h3>
          <ul>
            {results.detections.map((d, i) => (
              <li key={i}>{d.class} ({(d.confidence * 100).toFixed(1)}%)</li>
            ))}
          </ul>
          <h4>OCR 텍스트:</h4>
          <p>{results.ocr_text}</p>
          <h4>Gemini 추론:</h4>
          <p>{results.gemini_result}</p>
        </div>
      )}
    </div>
  );
};

export default MainPage;

