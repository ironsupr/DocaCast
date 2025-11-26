import { motion } from "motion/react";
import type { ReactNode } from "react";

type SwitchProps = {
  value: boolean;
  onToggle: () => void;
  iconOn: ReactNode;
  iconOff: ReactNode;
};

export function Switch({
  value,
  onToggle,
  iconOn,
  iconOff,
}: SwitchProps) {
  return (
    <button
      onClick={onToggle}
      style={{
        display: 'flex',
        width: 52,
        padding: 3,
        borderRadius: 999,
        border: value ? '1px solid #333' : 'none',
        cursor: 'pointer',
        background: value ? '#000000' : 'var(--bg-tertiary)',
        justifyContent: value ? 'flex-end' : 'flex-start',
        transition: 'background 0.3s ease, border 0.3s ease',
      }}
    >
      <motion.div
        layout
        transition={{
          type: "spring",
          duration: 0.5,
          bounce: 0.2,
        }}
        style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          width: 26,
          height: 26,
          borderRadius: '50%',
          background: 'var(--bg-primary)',
          boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
        }}
      >
        {value ? (
          <motion.div
            key="on"
            initial={{ opacity: 0, rotate: -60, scale: 0.5 }}
            animate={{ opacity: 1, rotate: 0, scale: 1 }}
            exit={{ opacity: 0, rotate: 60, scale: 0.5 }}
            transition={{ duration: 0.25 }}
            style={{
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              color: 'var(--accent-primary)',
            }}
          >
            {iconOn}
          </motion.div>
        ) : (
          <motion.div
            key="off"
            initial={{ opacity: 0, rotate: 60, scale: 0.5 }}
            animate={{ opacity: 1, rotate: 0, scale: 1 }}
            exit={{ opacity: 0, rotate: -60, scale: 0.5 }}
            transition={{ duration: 0.25 }}
            style={{
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              color: 'var(--text-muted)',
            }}
          >
            {iconOff}
          </motion.div>
        )}
      </motion.div>
    </button>
  );
}

export default Switch;
