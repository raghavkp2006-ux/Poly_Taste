export function TopographicBackground() {
  return (
    <div className="fixed inset-0 z-[-1] pointer-events-none overflow-hidden" style={{ backgroundColor: "#10262A" }}>
      {/* 
        CSS-only Topographic effect using repeating radial gradients with distortion.
        This provides a highly performant, lightweight background.
      */}
      <style dangerouslySetInnerHTML={{ __html: `
        @keyframes drift1 {
          0% { transform: translate(0, 0) scale(1); }
          50% { transform: translate(3%, 4%) scale(1.05); }
          100% { transform: translate(0, 0) scale(1); }
        }
        @keyframes drift2 {
          0% { transform: translate(0, 0) scale(1); }
          50% { transform: translate(-4%, 2%) scale(1.1); }
          100% { transform: translate(0, 0) scale(1); }
        }
        @keyframes colorShift {
          0% { filter: hue-rotate(0deg); }
          100% { filter: hue-rotate(360deg); }
        }
        .topo-layer {
          position: absolute;
          inset: -20%;
          opacity: 0.15;
          mix-blend-mode: screen;
        }
        .topo-1 {
          background-image: repeating-radial-gradient(ellipse at 40% 50%, transparent 0, transparent 20px, #C6318C 20px, #C6318C 21px);
          animation: drift1 30s ease-in-out infinite;
        }
        .topo-2 {
          background-image: repeating-radial-gradient(ellipse at 60% 40%, transparent 0, transparent 30px, #E8A23D 30px, #E8A23D 31px);
          animation: drift2 40s ease-in-out infinite reverse;
        }
        .topo-3 {
          background-image: repeating-radial-gradient(ellipse at 50% 60%, transparent 0, transparent 40px, #B23A2E 40px, #B23A2E 41px);
          animation: drift1 35s ease-in-out infinite;
          opacity: 0.1;
        }
        
        @media (prefers-reduced-motion: reduce) {
          .topo-1, .topo-2, .topo-3 {
            animation: none;
          }
        }
      `}} />
      <div className="topo-layer topo-1" />
      <div className="topo-layer topo-2" />
      <div className="topo-layer topo-3" />
      
      {/* Vignette to soften the edges and focus center */}
      <div className="absolute inset-0" style={{ background: "radial-gradient(ellipse at center, transparent 0%, #10262A 80%)" }} />
    </div>
  )
}
