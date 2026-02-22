import { memo } from 'react';
import { motion } from 'framer-motion';
import { buttonMotionProps } from '../animations/variants';

function Button({
  variant = 'primary',
  type = 'button',
  className = '',
  children,
  ...rest
}) {
  return (
    <motion.button
      type={type}
      className={`btn btn-${variant} ${className}`.trim()}
      {...buttonMotionProps}
      {...rest}
    >
      {children}
    </motion.button>
  );
}

export default memo(Button);
