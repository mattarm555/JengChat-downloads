"""Generate one Pages deployment from verified public release assets; never from drafts."""
import argparse,hashlib,html,json,pathlib,urllib.request,urllib.parse,shutil
REPO='mattarm555/JengChat-downloads'
def get(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'JengChat-delivery'}),timeout=120) as r: return r.read()
def generate(release,fetch,template,output):
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
    (output/'updates').mkdir(exist_ok=True)
    (output/'updates'/('releases.'+channel+'.json')).write_text(json.dumps(feed,indent=2)+'\n',encoding='utf-8')
    (output/'updates/source.txt').write_text('https://github.com/'+REPO+'/releases/download/'+release['tag_name']+'/\n',encoding='utf-8')
    info={'version':meta['version'],'installer':assets[meta['installer']]['browser_download_url'],'sha256':meta['installer_sha256'],
          'notes':meta['notes'],'release_url':release['html_url'],'commit':meta['commit']}
    (output/'release.json').write_text(json.dumps(info,indent=2)+'\n',encoding='utf-8')
    print('Verified assets and generated page/feed for '+meta['version'])
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--tag',required=True);p.add_argument('--template',required=True);p.add_argument('--output',required=True)
    args=p.parse_args()
    release=json.loads(get('https://api.github.com/repos/'+REPO+'/releases/tags/'+urllib.parse.quote(args.tag,safe='')))
    generate(release,get,args.template,args.output)
