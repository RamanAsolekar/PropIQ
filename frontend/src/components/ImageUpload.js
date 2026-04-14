// PropIQ ImageUpload Component
import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';

export default function ImageUpload({ onImageSelect, image }) {
  const [preview, setPreview] = useState(null);

  const onDrop = useCallback((files) => {
    const file = files[0];
    if (!file) return;
    const url = URL.createObjectURL(file);
    setPreview(url);
    onImageSelect(file);
  }, [onImageSelect]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop, accept: { 'image/*': ['.jpg', '.jpeg', '.png', '.webp'] },
    maxFiles: 1, maxSize: 10 * 1024 * 1024,
  });

  const clear = (e) => {
    e.stopPropagation();
    setPreview(null);
    onImageSelect(null);
    if (preview) URL.revokeObjectURL(preview);
  };

  return (
    <div style={{ padding: '0 20px 16px' }}>
      <div style={{ fontSize: 11, fontWeight: 600, color: '#5F5E5A',
        textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8 }}>
        Property Photo <span style={{ color: '#888780', fontWeight: 400,
          textTransform: 'none', letterSpacing: 0 }}>(optional — enables CV scoring)</span>
      </div>

      {preview ? (
        <div style={{ position: 'relative', borderRadius: 10, overflow: 'hidden',
          border: '1px solid rgba(44,44,42,0.12)' }}>
          <img src={preview} alt="Property" style={{ width: '100%', height: 140,
            objectFit: 'cover', display: 'block' }} />
          <div style={{ position: 'absolute', inset: 0, background: 'rgba(0,0,0,0.3)',
            display: 'flex', alignItems: 'flex-end', padding: 10, justifyContent: 'space-between' }}>
            <div style={{ background: '#0F6E56', color: '#fff', fontSize: 11, fontWeight: 600,
              padding: '3px 10px', borderRadius: 20 }}>CV Analysis Active</div>
            <button onClick={clear} style={{ background: 'rgba(0,0,0,0.5)', color: '#fff',
              border: 'none', borderRadius: 20, padding: '3px 10px', fontSize: 11,
              cursor: 'pointer', fontFamily: 'Inter, sans-serif' }}>Remove</button>
          </div>
        </div>
      ) : (
        <div {...getRootProps()} style={{
          border: `2px dashed ${isDragActive ? '#534AB7' : 'rgba(44,44,42,0.18)'}`,
          borderRadius: 10, padding: '20px 16px', textAlign: 'center', cursor: 'pointer',
          background: isDragActive ? '#EEEDFE' : '#F7F6F2', transition: 'all 0.15s',
        }}>
          <input {...getInputProps()} />
          <div style={{ fontSize: 24, marginBottom: 6 }}>📷</div>
          <div style={{ fontSize: 12, fontWeight: 500, color: '#534AB7', marginBottom: 3 }}>
            {isDragActive ? 'Drop the photo here...' : 'Upload property photo'}
          </div>
          <div style={{ fontSize: 11, color: '#888780' }}>
            CLIP AI will assess condition · JPG, PNG up to 10MB
          </div>
        </div>
      )}
    </div>
  );
}