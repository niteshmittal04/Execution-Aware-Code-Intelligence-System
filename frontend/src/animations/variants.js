export const panelEnter = {
  hidden: { opacity: 0, y: 12 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.2, ease: 'easeOut' },
  },
};

export const sidebarMotion = {
  collapsed: {
    x: '-100%',
    opacity: 0.98,
    transition: { duration: 0.18, ease: 'easeOut' },
  },
  expanded: {
    x: '0%',
    opacity: 1,
    transition: { duration: 0.2, ease: 'easeOut' },
  },
};

export const nodeEnter = {
  hidden: { opacity: 0, scale: 0.96 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: { duration: 0.16, ease: 'easeOut' },
  },
};

export const buttonMotionProps = {
  whileHover: { scale: 1.02 },
  whileTap: { scale: 0.98 },
  transition: { duration: 0.12, ease: 'easeOut' },
};
