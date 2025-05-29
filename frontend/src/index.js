// import React from 'react';
// import ReactDOM from 'react-dom/client';
// import './index.css';
// import App from './App';

// // React 18 방식으로 루트 엘리먼트 생성
// const root = ReactDOM.createRoot(document.getElementById('root'));

// // App 컴포넌트 렌더링
// root.render(
//   <React.StrictMode>
//     <App />
//   </React.StrictMode>
// );
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

// React 18 방식으로 루트 엘리먼트 생성
const root = ReactDOM.createRoot(document.getElementById('root'));

// App 컴포넌트 렌더링
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);