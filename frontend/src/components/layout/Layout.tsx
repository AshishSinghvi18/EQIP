import React from 'react';
import { Outlet } from 'react-router-dom';
import Header from './Header';
import Sidebar from './Sidebar';

function Layout() {
  return (
    <div className="mx-auto flex min-h-screen max-w-[1600px] flex-col gap-6 px-4 py-6 md:px-6 xl:flex-row xl:px-8">
      <Sidebar />
      <div className="min-w-0 flex-1">
        <Header />
        <main className="pb-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export default Layout;
