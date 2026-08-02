

export function AmbientBackground() {
  return (
    <div
      className="fixed inset-0 pointer-events-none z-0"
      aria-hidden="true"
      style={{ backgroundColor: "#0A0E14" }}
    >
      <div
        style={{
          position: "absolute",
          top: "-10%", left: "-5%",
          width: "55vw", height: "55vw",
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(124,108,240,0.25) 0%, transparent 70%)",
          filter: "blur(80px)",
        }}
      />
      <div
        style={{
          position: "absolute",
          top: "-5%", right: "-10%",
          width: "50vw", height: "50vw",
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(255,122,89,0.18) 0%, transparent 70%)",
          filter: "blur(90px)",
        }}
      />
      <div
        style={{
          position: "absolute",
          bottom: "-15%", left: "30%",
          width: "48vw", height: "48vw",
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(227,168,87,0.15) 0%, transparent 70%)",
          filter: "blur(100px)",
        }}
      />
      {/* Vignette */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: "radial-gradient(ellipse 80% 70% at 50% 40%, transparent 0%, #0A0E14 85%)",
        }}
      />
    </div>
  )
}
