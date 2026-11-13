import type { ButtonHTMLAttributes } from 'react';
import { LoaderCircle } from 'lucide-react';

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'secondary' | 'ghost';
  loading?: boolean;
};
export function Button({
  variant = 'primary',
  loading,
  className = '',
  children,
  disabled,
  ...props
}: Props) {
  return (
    <button
      {...props}
      disabled={disabled || loading}
      className={`button button-${variant} ${className}`}
    >
      {loading ? (
        <LoaderCircle size={18} className="spinner" aria-hidden="true" />
      ) : null}
      {children}
    </button>
  );
}
