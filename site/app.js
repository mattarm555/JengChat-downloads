'use strict';
const $ = (id) => document.getElementById(id);
const RELEASES = '/mattarm555/JengChat-downloads/releases/';

// Release: version, installer, checksum and notes come from release.json,
// which publish_delivery.py writes. Links are accepted only from this repository's releases.
(async () => {
  try {
    const response = await fetch('release.json', { cache: 'no-store' });
    if (!response.ok) throw Error('Release unavailable');
    const info = await response.json();
    const download = new URL(info.installer);
    if (download.origin !== 'https://github.com' || !download.pathname.startsWith(RELEASES + 'download/'))
      throw Error('Invalid installer link');
    $('version').textContent = 'Version ' + info.version + ' · Windows 10 and 11, 64-bit · free';
    document.querySelectorAll('[data-version]').forEach((el) => { el.textContent = 'Version ' + info.version; });
    const button = $('download-button');
    button.href = download.href;
    button.hidden = false;
    $('status').textContent = 'Install it once. After that, JengChat asks before it updates itself.';
    $('notes').textContent = info.notes;
    $('checksum').textContent = info.sha256;
    const url = new URL(info.release_url);
    if (url.origin === 'https://github.com' && url.pathname.startsWith(RELEASES)) {
      $('release').href = url.href;
      $('release').hidden = false;
    }
  } catch {
    $('version').textContent = "The download isn't available right now.";
    $('status').textContent = 'Try this page again in a little while. A JengChat you already installed keeps working.';
  }
})();

// Live status: an https feed returning
// {"server":"online"|"offline","players":["name",...] or null,"updated":"ISO time"}.
(() => {
  const meta = document.querySelector('meta[name="jengchat-status"]');
  const source = meta && meta.content.trim();
  const panel = $('live');
  if (!source || !panel) return;
  let feed;
  try {
    feed = new URL(source, location.href);
    if (feed.protocol !== 'https:' && feed.origin !== location.origin) return;
  } catch { return; }

  const COLOURS = ['#e7be65', '#e76c60', '#7fc7a0', '#8fb8e8', '#e8a56f', '#d9d2bf'];
  const colour = (name) => COLOURS[[...name].reduce((a, c) => a + c.charCodeAt(0), 0) % COLOURS.length];
  const time = new Intl.DateTimeFormat(undefined, { hour: 'numeric', minute: '2-digit' });

  function show(state, serverText, countHtml, people, updated) {
    panel.dataset.state = state;
    $('live-server').textContent = serverText;
    $('live-count').replaceChildren(...countHtml);
    $('live-people').replaceChildren(...people.map((name) => {
      const li = document.createElement('li');
      const dot = document.createElement('span');
      dot.style.setProperty('--c', colour(name));
      dot.textContent = name.slice(0, 1).toUpperCase();
      dot.setAttribute('aria-hidden', 'true');
      li.append(dot, name);
      return li;
    }));
    $('live-time').textContent = updated;
  }

  async function poll() {
    try {
      const response = await fetch(feed.href, { cache: 'no-store', credentials: 'omit' });
      if (!response.ok) throw Error('feed');
      const data = await response.json();
      const listed = Array.isArray(data.players);
      const players = listed
        ? data.players.filter((p) => typeof p === 'string' && p.length > 0 && p.length <= 32).slice(0, 60)
        : [];
      const at = new Date(data.updated);
      const fresh = !isNaN(at) && Date.now() - at.getTime() < 5 * 60 * 1000;
      const stamp = isNaN(at) ? '' : 'Updated ' + time.format(at) + (fresh ? '' : ' · this may be out of date');
      if (data.server !== 'online') {
        show('offline', 'Server offline', [document.createTextNode('The server is down right now. Check back soon.')], [], stamp);
        return;
      }
      if (!listed) {
        show('online', 'Server online', [document.createTextNode("The player list isn't available right now.")], [], stamp);
        return;
      }
      const b = document.createElement('b');
      b.textContent = String(players.length);
      const words = players.length === 1 ? 'friend online' : 'friends online';
      const rest = document.createTextNode(players.length ? words : 'friends online. Be the first one in.');
      show('online', 'Server online', [b, rest], players, stamp);
    } catch {
      show('unknown', 'Status unavailable', [document.createTextNode("Couldn't load the live list just now.")], [], '');
    }
  }

  poll();
  setInterval(() => { if (!document.hidden) poll(); }, 30000);
})();

// The one moment: the three table screenshots are dealt onto the felt once.
(() => {
  const deal = document.querySelector('[data-moment="deal"]');
  if (!deal || !('IntersectionObserver' in window) || matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const rect = deal.getBoundingClientRect();
  if (rect.top < innerHeight) return; // already on screen: leave it at rest
  deal.classList.add('is-dealing');
  const seen = new IntersectionObserver((entries) => {
    if (!entries.some((e) => e.isIntersecting)) return;
    seen.disconnect();
    requestAnimationFrame(() => {
      deal.classList.add('is-dealt');
      deal.classList.remove('is-dealing');
    });
  }, { threshold: 0.25 });
  seen.observe(deal);
})();
