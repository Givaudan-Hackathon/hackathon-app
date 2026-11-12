import { useEffect, useId, useRef, type ReactNode } from 'react';
import { X } from 'lucide-react';

export function Dialog({
  open,
  onClose,
  title,
  children,
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  useEffect(() => {
    const dialog = ref.current;
    if (open && !dialog?.open) dialog?.showModal();
    if (!open && dialog?.open) dialog.close();
    return () => {
      if (dialog?.open) dialog.close();
    };
  }, [open]);
  return (
    <dialog
      ref={ref}
      className="dialog"
      aria-labelledby={titleId}
      onCancel={onClose}
      onClick={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div className="dialog-content">
        <button
          className="icon-button dialog-close"
          onClick={onClose}
          aria-label="Fermer"
        >
          <X size={22} aria-hidden="true" />
        </button>
        <h2 id={titleId}>{title}</h2>
        {children}
      </div>
    </dialog>
  );
}
