"""Generate one Pages deployment from verified public release assets; never from drafts."""
import argparse,hashlib,html,json,pathlib,urllib.request,urllib.parse,urllib.error,shutil
REPO='mattarm555/JengChat-downloads'
SITE='https://mattarm555.github.io/JengChat-downloads/'
# JengParty (its own private source repo) is published here too, under party/ with party-v<version> tags.
PARTY_FEED=SITE+'party/'
PARTY_CHANNEL='party-win-x64'
PARTY_WAIVERS=()  # owner-approved one-time second-machine pilot waivers for JengParty tags: none
def get(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'JengChat-delivery'}),timeout=120) as r: return r.read()
def release_of(tag):
    return json.loads(get('https://api.github.com/repos/'+REPO+'/releases/tags/'+urllib.parse.quote(tag,safe='')))
def verified_assets(release,fetch):
    '''Every asset of a published prerelease, from this repository only, checked against SHA256SUMS.txt.'''
    if release.get('draft') or not release.get('prerelease'): raise ValueError('Select a published friends-testing prerelease')
    assets={a['name']:a for a in release['assets']}
    def asset(name):
        a=assets[name]
        expected='https://github.com/'+REPO+'/releases/download/'+release['tag_name']+'/'
        if not a['browser_download_url'].startswith(expected): raise ValueError('Unexpected release asset origin')
        return fetch(a['browser_download_url'])
    checks={line.split('  ',1)[1]:line.split('  ',1)[0] for line in asset('SHA256SUMS.txt').decode().splitlines()}
    blobs={}
    for name,expected in checks.items():
        if pathlib.PurePosixPath(name).name!=name: raise ValueError('Invalid asset name')
        body=asset(name)
        if hashlib.sha256(body).hexdigest()!=expected: raise ValueError('Corrupt asset '+name)
        blobs[name]=body
    return assets,checks,blobs
def verify_party(release,fetch,pilot_check='passed'):
    '''Checks a published JengParty prerelease as strictly as JengChat's; returns what write_party needs.'''
    if pilot_check not in ('passed','waived'): raise ValueError('Invalid pilot acceptance status')
    if pilot_check=='waived' and release['tag_name'] not in PARTY_WAIVERS: raise ValueError('No pilot waiver is approved for this JengParty release')
    if not release['tag_name'].startswith('party-v'): raise ValueError('JengParty releases are tagged party-v<version>')
    assets,checks,blobs=verified_assets(release,fetch)
    meta=json.loads(blobs['release-metadata.json'])
    if meta.get('development') or meta.get('game')!='jengparty' or meta.get('feed')!=PARTY_FEED: raise ValueError('Test builds and other games cannot enter the JengParty feed')
    if release['tag_name']!='party-v'+meta['version']: raise ValueError('Version/tag mismatch')
    feed=json.loads(blobs['releases.'+PARTY_CHANNEL+'.json'])
    if not feed.get('Assets'): raise ValueError('Missing full package')
    for a in feed['Assets']:
        if a['Type']!='Full' or a['Version']!=meta['version'] or a['PackageId']!='JengParty': raise ValueError('Unexpected feed entry')
        body=blobs[a['FileName']]
        if a['SHA256'].lower()!=hashlib.sha256(body).hexdigest() or a['Size']!=len(body): raise ValueError('Package/feed mismatch')
    if meta['installer_sha256']!=checks[meta['installer']]: raise ValueError('Installer checksum mismatch')
    return {'tag':release['tag_name'],'feed':feed,'info':{'tag':release['tag_name'],'version':meta['version'],
        'installer':assets[meta['installer']]['browser_download_url'],'sha256':meta['installer_sha256'],'size':len(blobs[meta['installer']]),
        'notes':meta['notes'],'release_url':release['html_url'],'commit':meta['commit'],
        'acceptance':{'second_machine_install_update':pilot_check}}}
def write_party(output,party):
    '''party/: JengParty's update feed (source.txt) and release.json, which JengChat's Get JengParty reads.'''
    folder=pathlib.Path(output)/'party'; folder.mkdir(parents=True,exist_ok=True)
    (folder/('releases.'+PARTY_CHANNEL+'.json')).write_text(json.dumps(party['feed'],indent=2)+'\n',encoding='utf-8')
    (folder/'source.txt').write_text('https://github.com/'+REPO+'/releases/download/'+party['tag']+'/\n',encoding='utf-8')
    (folder/'release.json').write_text(json.dumps(party['info'],indent=2)+'\n',encoding='utf-8')
def live_party(fetch):
    '''(tag, pilot check) of the JengParty release the live site serves, or None before the first one.'''
    try: page=json.loads(fetch(SITE+'party/release.json'))
    except urllib.error.HTTPError as e:
        if e.code==404: return None
        raise
    return page['tag'],page['acceptance']['second_machine_install_update']
def live_jengchat(fetch):
    '''(tag, pilot check, settings check) of the JengChat release the live site serves.'''
    try: page=json.loads(fetch(SITE+'release.json'))
    except urllib.error.HTTPError as e:
        if e.code==404: raise ValueError('The live site has no JengChat release to keep')
        raise
    acceptance=page.get('acceptance')
    if not acceptance: raise ValueError('The live JengChat release records no acceptance')
    return 'v'+page['version'],acceptance['second_machine_install_update'],acceptance['second_machine_settings']
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
def generate(release,fetch,template,output,settings_check=None,pilot_check='passed',party=None):
    if pilot_check not in ('passed','waived'): raise ValueError('Invalid pilot acceptance status')
    # Owner-approved one-time waivers: beta 5, and 3.0.0-beta.1 (the Raylib-to-Godot update can only be
    # exercised against the live feed, so it was released untested on a second machine), and 3.0.0-beta.2
    # (waived by the owner on 2026-11-25).
    if pilot_check=='waived' and release['tag_name'] not in ('v2.1.0-beta.5','v3.0.0-beta.1','v3.0.0-beta.2'): raise ValueError('Pilot waiver is approved for beta 5, 3.0.0-beta.1 and 3.0.0-beta.2 only')
    # Verify every asset before moving the public page/feed forward.
    assets,checks,blobs=verified_assets(release,fetch)
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
    if party is not None: write_party(output,party)
    print('Verified assets and generated page/feed for '+meta['version']+('' if party is None else ', with JengParty '+party['info']['version']))
if __name__=='__main__':
    # One Pages deployment holds both games. Publishing JengChat (--tag) keeps the live JengParty release;
    # publishing JengParty (--party-tag) keeps the live JengChat release. Whatever is kept is verified again.
    p=argparse.ArgumentParser();p.add_argument('--tag');p.add_argument('--template',required=True);p.add_argument('--output',required=True)
    p.add_argument('--settings-check',choices=['verified','waived'])
    p.add_argument('--pilot-check',choices=['passed','waived'],default='passed')
    p.add_argument('--party-tag');p.add_argument('--party-pilot-check',choices=['passed','waived'],default='passed')
    args=p.parse_args()
    if bool(args.tag)==bool(args.party_tag): p.error('give exactly one of --tag (JengChat) or --party-tag (JengParty)')
    if args.party_tag:
        party=verify_party(release_of(args.party_tag),get,args.party_pilot_check)
        tag,pilot,settings=live_jengchat(get)
    else:
        if not args.settings_check: p.error('--settings-check is required with --tag')
        tag,pilot,settings=args.tag,args.pilot_check,args.settings_check
        live=live_party(get)
        party=None if live is None else verify_party(release_of(live[0]),get,live[1])
    generate(release_of(tag),get,args.template,args.output,settings,pilot,party)
