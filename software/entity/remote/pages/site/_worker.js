const hosts = new Set(["entity.livinginacat.world", "entity-alfonsito.pages.dev"]);
const publicAssets = new Set(["/ui/portal.css", "/ui/portal.js", "/ui/tasks.js", "/ui/dashboard-nav.css", "/ui/camera.js", "/ui/shortcuts.js", "/ui/iphone.webmanifest", "/ui/iphone-qr.png", "/ui/alfonsito-180.png", "/ui/alfonsito-192.png", "/ui/alfonsito-512.png", "/ui/iphone-pair.js", "/ui/iphone-ready.js", "/ui/reconnect.js", "/ui/sentient.svg", "/ui/space-grotesk.ttf", "/ui/OFL.txt"]);

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (!hosts.has(url.hostname)) return new Response("Not found", { status: 404 });
    if (publicAssets.has(url.pathname) && ["GET", "HEAD"].includes(request.method)) {
      return env.ASSETS.fetch(request);
    }
    return env.OPERATOR.fetch(request);
  },
};
