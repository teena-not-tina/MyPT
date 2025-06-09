import React from 'react';
import NavigationBar from './NavigationBar';

// 레이아웃 컴포넌트
function Layout({ children }) {
  return (
    <>
      <NavigationBar />
      <main style={{ minHeight: 'calc(100vh - 60px)' }}>
        {children}
      </main>
    </>
  );
}

export default Layout;