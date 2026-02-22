import { memo } from 'react';

function AppLayout({ topNavigation, workspace, statusBar }) {
  return (
    <div className="app-layout">
      {topNavigation}
      {workspace}
      {statusBar}
    </div>
  );
}

export default memo(AppLayout);
