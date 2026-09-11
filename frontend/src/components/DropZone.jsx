import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'

/**
 * Drag-and-drop image upload zone.
 * Props:
 *   onFileSelected(file: File): void
 */
export default function DropZone({ onFileSelected, disabled }) {
  const [dragging, setDragging] = useState(false)

  const onDrop = useCallback((accepted) => {
    setDragging(false)
    if (accepted[0]) onFileSelected(accepted[0])
  }, [onFileSelected])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': ['.jpg', '.jpeg', '.png', '.webp'] },
    multiple: false,
    disabled,
    onDragEnter: () => setDragging(true),
    onDragLeave: () => setDragging(false),
  })

  return (
    <div
      {...getRootProps()}
      id="upload-dropzone"
      className={`dropzone${isDragActive || dragging ? ' active' : ''}`}
      aria-label="Image upload area"
    >
      <input {...getInputProps()} id="upload-file-input" />
      <span className="dropzone-icon">📸</span>
      {isDragActive ? (
        <h3>Drop your leaf photo here…</h3>
      ) : (
        <>
          <h3>Drag & drop a leaf photo</h3>
          <p>or <strong style={{ color: 'var(--leaf)' }}>click to browse</strong></p>
          <p style={{ marginTop: '0.5rem' }}>JPG, PNG, WebP · max 10 MB</p>
        </>
      )}
    </div>
  )
}
