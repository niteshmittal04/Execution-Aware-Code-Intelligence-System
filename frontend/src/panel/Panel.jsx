import { memo } from 'react';
import { motion } from 'framer-motion';
import { panelEnter } from '../animations/variants';

function Panel({ as = 'div', className = '', children, ...rest }) {
  const Component = motion[as] || motion.div;
  return (
    <Component
      className={`panel ${className}`.trim()}
      variants={panelEnter}
      initial="hidden"
      animate="visible"
      {...rest}
    >
      {children}
    </Component>
  );
}

export default memo(Panel);
