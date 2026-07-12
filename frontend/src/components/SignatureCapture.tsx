import React, { useRef, useState } from 'react';
import { Trash2, Download, Undo2 } from 'lucide-react';
import { Button } from './ui/Button';

interface SignatureCaptureProps {
  onCapture: (signatureData: string) => void;
  existingSignature?: string;
  disabled?: boolean;
}

export const SignatureCapture: React.FC<SignatureCaptureProps> = ({
  onCapture,
  existingSignature,
  disabled = false,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [mode, setMode] = useState<'draw' | 'view'>('draw');
  const [undoStack, setUndoStack] = useState<string[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const getCanvasPoint = (e: React.PointerEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return { x: 0, y: 0 };
    const rect = canvas.getBoundingClientRect();
    return {
      x: (e.clientX - rect.left) * (canvas.width / rect.width),
      y: (e.clientY - rect.top) * (canvas.height / rect.height),
    };
  };

  const saveStroke = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    setUndoStack((prev) => [...prev, canvas.toDataURL()]);
  };

  const startDrawing = (e: React.PointerEvent<HTMLCanvasElement>) => {
    if (disabled || mode === 'view') return;
    e.preventDefault();
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    saveStroke();
    const pt = getCanvasPoint(e);
    ctx.beginPath();
    ctx.moveTo(pt.x, pt.y);
    setIsDrawing(true);
  };

  const draw = (e: React.PointerEvent<HTMLCanvasElement>) => {
    if (!isDrawing || disabled || mode === 'view') return;
    e.preventDefault();
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.strokeStyle = '#000000';
    ctx.lineWidth = 2;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    const pt = getCanvasPoint(e);
    ctx.lineTo(pt.x, pt.y);
    ctx.stroke();
  };

  const stopDrawing = (e: React.PointerEvent<HTMLCanvasElement>) => {
    if (!isDrawing) return;
    e.preventDefault();
    setIsDrawing(false);
  };

  const undo = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    if (undoStack.length === 0) return;
    const prevState = undoStack[undoStack.length - 1];
    setUndoStack((prev) => prev.slice(0, -1));
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    if (undoStack.length > 1) {
      const img = new Image();
      img.onload = () => ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      img.src = prevState;
    }
  };

  const clearCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    setUndoStack([]);
  };

  const saveSignature = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const signatureData = canvas.toDataURL('image/png');
    onCapture(signatureData);
    setMode('view');
  };

  const downloadSignature = () => {
    if (!existingSignature && mode === 'draw') return;
    const link = document.createElement('a');
    link.href = existingSignature || canvasRef.current?.toDataURL('image/png') || '';
    link.download = 'signature.png';
    link.click();
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => {
      const data = event.target?.result as string;
      onCapture(data);
      setMode('view');
      const img = new Image();
      img.onload = () => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      };
      img.src = data;
    };
    reader.readAsDataURL(file);
  };

  React.useEffect(() => {
    if (existingSignature && mode === 'view') {
      const img = new Image();
      img.onload = () => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      };
      img.src = existingSignature;
    }
  }, [existingSignature, mode]);

  return (
    <div className="space-y-4">
      <div className="flex gap-2 flex-wrap">
        {mode === 'draw' && (
          <>
            <Button
              type="button"
              onClick={saveSignature}
              disabled={disabled}
              className="px-3 py-2 bg-success text-white hover:bg-success/90 text-sm disabled:opacity-50"
            >
              Save Signature
            </Button>
            <Button
              type="button"
              onClick={undo}
              disabled={disabled || undoStack.length === 0}
              className="px-3 py-2 border border-neutral-300 text-neutral-700 hover:bg-neutral-50 text-sm flex items-center gap-1 disabled:opacity-40"
            >
              <Undo2 className="w-4 h-4" />
              Undo
            </Button>
            <Button
              type="button"
              onClick={clearCanvas}
              disabled={disabled}
              className="px-3 py-2 border border-error text-error hover:bg-error/10 text-sm"
            >
              <Trash2 className="w-4 h-4" />
              Clear
            </Button>
          </>
        )}
        {mode === 'view' && (
          <>
            <Button
              type="button"
              onClick={() => { setMode('draw'); setUndoStack([]); }}
              disabled={disabled}
              className="px-3 py-2 bg-primary-600 text-white hover:bg-primary-700 text-sm disabled:opacity-50"
            >
              Redraw
            </Button>
            <Button
              type="button"
              onClick={downloadSignature}
              disabled={disabled}
              className="px-3 py-2 border border-neutral-300 text-neutral-700 hover:bg-neutral-50 text-sm flex items-center gap-1"
            >
              <Download className="w-4 h-4" />
              Download
            </Button>
          </>
        )}
      </div>

      <canvas
        ref={canvasRef}
        width={400}
        height={150}
        onPointerDown={startDrawing}
        onPointerMove={draw}
        onPointerUp={stopDrawing}
        onPointerLeave={stopDrawing}
        className={`border-2 border-dashed border-neutral-300 rounded-lg bg w-full touch-none ${
          disabled || mode === 'view' ? 'cursor-default' : 'cursor-crosshair'
        }`}
        style={{ maxWidth: '100%', height: 'auto' }}
      />

      <div className="text-xs text-neutral-600">
        {mode === 'draw' ? (
          <p>Draw your signature above using your mouse, stylus, or finger</p>
        ) : (
          <p>✓ Signature saved. Click "Redraw" to change it.</p>
        )}
      </div>

      <div className="flex items-center gap-2">
        <input
          ref={fileInputRef}
          type="file"
          accept="image/png,image/jpeg,image/jpg"
          className="hidden"
          onChange={handleFileUpload}
          disabled={disabled || mode === 'view'}
        />
        <Button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={disabled || mode === 'view'}
          className="px-3 py-2 border border-neutral-300 text-neutral-700 hover:bg-neutral-50 text-sm"
        >
          or Upload Image
        </Button>
      </div>
    </div>
  );
};
