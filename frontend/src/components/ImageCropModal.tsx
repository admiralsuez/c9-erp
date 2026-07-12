import React, { useRef, useState, useEffect, useCallback } from 'react';

interface Props {
  file: File;
  onConfirm: (croppedFile: File) => void;
  onCancel: () => void;
}

export const ImageCropModal: React.FC<Props> = ({ file, onConfirm, onCancel }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imageRef = useRef<HTMLImageElement | null>(null);
  const [rotation, setRotation] = useState(0);
  const [imgLoaded, setImgLoaded] = useState(false);
  const [canvasSize, setCanvasSize] = useState(400);

  const sizeRef = useRef(200);
  const posRef = useRef({ x: 100, y: 100 });
  const dragRef = useRef(false);
  const dragOrigin = useRef({ x: 0, y: 0, cx: 0, cy: 0 });

  useEffect(() => {
    const img = new Image();
    img.onload = () => {
      imageRef.current = img;
      const maxD = 420;
      const side = Math.min(maxD, Math.max(img.width, img.height));
      setCanvasSize(side);
      const s = Math.round(side * 0.55);
      sizeRef.current = s;
      posRef.current = { x: Math.round((side - s) / 2), y: Math.round((side - s) / 2) };
      setImgLoaded(true);
    };
    img.src = URL.createObjectURL(file);
    return () => URL.revokeObjectURL(img.src);
  }, [file]);

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    const img = imageRef.current;
    if (!canvas || !img) return;

    canvas.width = canvasSize;
    canvas.height = canvasSize;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.fillStyle = '#f5f5f5';
    ctx.fillRect(0, 0, canvasSize, canvasSize);

    const scale = Math.min(canvasSize / img.width, canvasSize / img.height) * 0.85;
    const dw = img.width * scale;
    const dh = img.height * scale;

    ctx.save();
    ctx.translate(canvasSize / 2, canvasSize / 2);
    ctx.rotate((rotation * Math.PI) / 180);
    ctx.drawImage(img, -dw / 2, -dh / 2, dw, dh);
    ctx.restore();
  }, [canvasSize, rotation]);

  useEffect(() => { if (imgLoaded) draw(); }, [draw, imgLoaded]);

  const rotate90 = () => setRotation(r => (r + 90) % 360);

  const handleMouseDown = (e: React.MouseEvent) => {
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    const sx = (e.clientX - rect.left) * (canvasSize / rect.width);
    const sy = (e.clientY - rect.top) * (canvasSize / rect.height);
    const p = posRef.current;
    const s = sizeRef.current;
    if (sx < p.x || sx > p.x + s || sy < p.y || sy > p.y + s) return;
    dragRef.current = true;
    dragOrigin.current = { x: sx - p.x, y: sy - p.y, cx: p.x, cy: p.y };
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!dragRef.current) return;
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    const sx = (e.clientX - rect.left) * (canvasSize / rect.width);
    const sy = (e.clientY - rect.top) * (canvasSize / rect.height);
    const s = sizeRef.current;
    posRef.current = {
      x: Math.max(0, Math.min(sx - dragOrigin.current.x, canvasSize - s)),
      y: Math.max(0, Math.min(sy - dragOrigin.current.y, canvasSize - s)),
    };
    draw();
  };

  const handleMouseUp = () => { dragRef.current = false; };

  const handleConfirm = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const p = posRef.current;
    const s = sizeRef.current;

    const out = document.createElement('canvas');
    out.width = 300;
    out.height = 300;
    const octx = out.getContext('2d');
    if (!octx) return;
    octx.drawImage(canvas, p.x, p.y, s, s, 0, 0, 300, 300);

    out.toBlob(blob => {
      if (!blob) return;
      onConfirm(new File([blob], 'signature.png', { type: 'image/png' }));
    }, 'image/png');
  };

  const p = posRef.current;
  const s = sizeRef.current;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onMouseUp={handleMouseUp}>
      <div className="bg-white rounded-xl shadow-xl p-6 max-w-xl w-full mx-4">
        <h3 className="text-lg font-semibold mb-4">Crop & Rotate Signature</h3>

        <div className="relative mx-auto mb-4 bg-neutral-100 rounded-lg overflow-hidden flex items-center justify-center"
             style={{ width: canvasSize, height: canvasSize }}>
          <canvas
            ref={canvasRef}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            className="block cursor-move"
          />

          <div
            className="absolute border-2 border-primary-500 bg-primary-500/10 pointer-events-none"
            style={{
              left: p.x, top: p.y,
              width: s, height: s,
            }}
          />
        </div>

        <div className="flex items-center justify-between">
          <button
            onClick={rotate90}
            className="px-3 py-1.5 text-sm border border-neutral-300 rounded-lg hover:bg-neutral-50"
          >
            Rotate 90°
          </button>

          <div className="flex gap-2">
            <button
              onClick={onCancel}
              className="px-4 py-1.5 text-sm border border-neutral-300 rounded-lg hover:bg-neutral-50"
            >
              Cancel
            </button>
            <button
              onClick={handleConfirm}
              className="px-4 py-1.5 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-700"
            >
              Confirm
            </button>
          </div>
        </div>

        <p className="text-xs text-neutral-500 mt-3">
          Drag the square to reposition the crop area. Saved as 300×300 PNG.
        </p>
      </div>
    </div>
  );
};
