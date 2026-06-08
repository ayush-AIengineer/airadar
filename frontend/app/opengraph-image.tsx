import { ImageResponse } from "next/og";

export const alt = "AIRadar — Daily intelligence on newly launched AI tools";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OpengraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          padding: "80px",
          backgroundColor: "#05070d",
          backgroundImage:
            "radial-gradient(1200px 600px at 80% -10%, rgba(59,130,246,0.45), transparent)",
          color: "#e7ebf3",
          fontFamily: "sans-serif",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: 64,
              height: 64,
              borderRadius: 16,
              background: "#3b82f6",
              color: "#fff",
              fontSize: 40,
              fontWeight: 800,
            }}
          >
            A
          </div>
          <div style={{ fontSize: 34, fontWeight: 700 }}>AIRadar</div>
        </div>

        <div
          style={{
            marginTop: 36,
            fontSize: 76,
            fontWeight: 800,
            lineHeight: 1.05,
            maxWidth: 900,
            letterSpacing: "-0.02em",
          }}
        >
          The AI tool radar that never sleeps
        </div>

        <div style={{ marginTop: 28, fontSize: 30, color: "#93a4c0", maxWidth: 820 }}>
          Every AI product launching across the web — discovered, enriched, deduplicated and
          ranked. Updated daily.
        </div>
      </div>
    ),
    { ...size }
  );
}
