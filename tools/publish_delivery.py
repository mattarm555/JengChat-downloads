"""Generate one Pages deployment from verified public release assets; never from drafts."""
import argparse,hashlib,html,json,pathlib,urllib.request,urllib.parse,shutil
REPO='mattarm555/JengChat-downloads'
def get(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'JengChat-delivery'}),timeout=120) as r: return r.read()
def fingerprint(output):
    """Add ?v=<content hash> to the page's links to its own files, so browsers fetch a changed file
    instead of reusing an old copy (GitHub Pages lets them cache files for 10 minutes)."""
    import re
    output=pathlib.Path(output); page=output/'index.html'
    def tag(m):
        path=output/m.group(2)
        # Fonts keep the URL style.css loads them by, so their preloads still match.
        if '://' in m.group(2) or m.group(2).startswith('fonts/') or not path.is_file(): return m.group(0)
        return f'{m.group(1)}="{m.group(2)}?v={hashlib.sha256(path.read_bytes()).hexdigest()[:10]}"'
    page.write_text(re.sub(r'\b(href|src)="([A-Za-z0-9][A-Za-z0-9_./-]*)"',tag,page.read_text(encoding='utf-8')),encoding='utf-8')
def generate(release,fetch,template,output,settings_check=None,pilot_check='passed'):
    if pilot_check not in ('passed','waived'): raise ValueError('Invalid pilot acceptance status')
    # Owner-approved one-time waivers: beta 5, and 3.0.0-beta.1 (the Raylib-to-Godot update can only be
    # exercised against the live feed, so it was released untested on a second machine).
    if pilot_check=='waived' and release['tag_name'] not in ('v2.1.0-beta.5','v3.0.0-beta.1'): raise ValueError('Pilot waiver is approved for beta 5 and 3.0.0-beta.1 only')
    if release.get('draft') or not release.get('prerelease'): raise ValueError('Select a published friends-testing prerelease')
    assets={a['name']:a for a in release['assets']}
    def asset(name):
        a=assets[name]
        expected='https://github.com/'+REPO+'/releases/download/'+release['tag_name']+'/'
        if not a['browser_download_url'].startswith(expected): raise ValueError('Unexpected release asset origin')
        return fetch(a['browser_download_url'])
    checks={line.split('  ',1)[1]:line.split('  ',1)[0] for line in asset('SHA256SUMS.txt').decode().splitlines()}
    blobs={}
    # Verify every asset before moving the public page/feed forward.
    for name,expected in checks.items():
        if pathlib.PurePosixPath(name).name!=name: raise ValueError('Invalid asset name')
        body=asset(name)
        if hashlib.sha256(body).hexdigest()!=expected: raise ValueError('Corrupt asset '+name)
        blobs[name]=body
    meta=json.loads(blobs['release-metadata.json'])
    if meta.get('development') or meta['feed']!='https://mattarm555.github.io/JengChat-downloads/updates/': raise ValueError('Test builds cannot enter the friends feed')
    if release['tag_name']!='v'+meta['version']: raise ValueError('Version/tag mismatch')
    channel='friends-win-x64'; feed=json.loads(blobs['releases.'+channel+'.json'])
    if not feed.get('Assets'): raise ValueError('Missing full package')
    for a in feed['Assets']:
        if a['Type']!='Full' or a['Version']!=meta['version'] or a['PackageId']!='JengChat.Friends': raise ValueError('Unexpected feed entry')
        name=a['FileName']
        body=blobs[name]
        if a['SHA256'].lower()!=hashlib.sha256(body).hexdigest() or a['Size']!=len(body): raise ValueError('Package/feed mismatch')
        # Keep FileName as a basename: Velopack also uses it for the local cache path.
    if meta['installer_sha256']!=checks[meta['installer']]: raise ValueError('Installer checksum mismatch')
    output=pathlib.Path(output); output.mkdir(parents=True,exist_ok=True)
    shutil.copytree(template,output,dirs_exist_ok=True)
    fingerprint(output)
    (output/'updates').mkdir(exist_ok=True)
    (output/'updates'/('releases.'+channel+'.json')).write_text(json.dumps(feed,indent=2)+'\n',encoding='utf-8')
    (output/'updates/source.txt').write_text('https://github.com/'+REPO+'/releases/download/'+release['tag_name']+'/\n',encoding='utf-8')
    # Keep the initial pilot clients connected to the permanent release path.
    (output/'pilot').mkdir(exist_ok=True)
    (output/'pilot/source.txt').write_text((output/'updates/source.txt').read_text(encoding='utf-8'),encoding='utf-8')
    info={'version':meta['version'],'installer':assets[meta['installer']]['browser_download_url'],'sha256':meta['installer_sha256'],
          'notes':meta['notes'],'release_url':release['html_url'],'commit':meta['commit']}
    if settings_check is not None:
        if settings_check not in ('verified','waived'): raise ValueError('Invalid acceptance status')
        info['acceptance']={'second_machine_install_update':pilot_check,'second_machine_settings':settings_check}
    (output/'release.json').write_text(json.dumps(info,indent=2)+'\n',encoding='utf-8')
    print('Verified assets and generated page/feed for '+meta['version'])
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--tag',required=True);p.add_argument('--template',required=True);p.add_argument('--output',required=True)
    p.add_argument('--settings-check',choices=['verified','waived'],required=True)
    p.add_argument('--pilot-check',choices=['passed','waived'],default='passed')
    args=p.parse_args()
    release=json.loads(get('https://api.github.com/repos/'+REPO+'/releases/tags/'+urllib.parse.quote(args.tag,safe='')))
    generate(release,get,args.template,args.output,args.settings_check,args.pilot_check)
