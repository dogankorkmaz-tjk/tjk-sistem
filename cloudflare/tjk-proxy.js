// Cloudflare Worker: TJK muhtemeller verisini siteye CORS izniyle açar. Yalnız /muhtemeller/s/ yollarını geçirir.
export default {
  async fetch(req) {
    const u = new URL(req.url);
    const cors = { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "GET", "Cache-Control": "public, max-age=5" };
    if (req.method === "OPTIONS") return new Response(null, { headers: cors });
    if (!u.pathname.startsWith("/muhtemeller/s/") || u.pathname.includes("..")) return new Response("yok", { status: 404, headers: cors });
    const host = u.searchParams.get("cdn") === "0" ? "vhs-medya.tjk.org" : "vhs-medya-cdn.tjk.org";
    const r = await fetch(`https://${host}${u.pathname}`, { headers: { "User-Agent": "Mozilla/5.0", Accept: "application/json" }, cf: { cacheTtl: 5, cacheEverything: true } });
    return new Response(r.body, { status: r.status, headers: { ...cors, "Content-Type": "application/json" } });
  },
};
