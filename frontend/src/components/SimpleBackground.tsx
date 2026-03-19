'use client';

export default function SimpleBackground() {
  return (
    <div
      className="fixed inset-0 -z-10"
      style={{
        background: 'linear-gradient(to bottom, #0f172a, #1e293b)',
      }}
    />
  );
}
