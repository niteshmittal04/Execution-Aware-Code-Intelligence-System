import { memo } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { sidebarMotion } from '../animations/variants';

function WorkspaceContainer({ sidebar, children, isSidebarOpen, onCloseSidebar }) {
  return (
    <div className={isSidebarOpen ? 'workspace-container workspace-with-sidebar' : 'workspace-container workspace-no-sidebar'}>
      <AnimatePresence>
        {isSidebarOpen ? (
          <motion.aside
            className="sidebar"
            initial="collapsed"
            animate="expanded"
            exit="collapsed"
            variants={sidebarMotion}
          >
            {sidebar}
          </motion.aside>
        ) : null}
      </AnimatePresence>

      {isSidebarOpen ? <button className="sidebar-backdrop" onClick={onCloseSidebar} aria-label="Close sidebar" /> : null}

      <div className="main-panel">
        <div className="content-area">
          {children}
        </div>
      </div>
    </div>
  );
}

export default memo(WorkspaceContainer);
