"""Deploy a two-version pilot without advancing the normal friends update feed."""
import argparse,json,pathlib,hashlib,shutil,re
from publish_delivery import get,REPO
def verified(tag):
    if not re.fullmatch(r'v[0-9A-Za-z.-]+-pilot',tag):raise ValueError('A separate pilot tag is required')
    release=json.loads(get('https://api.github.com/repos/'+REPO+'/releases/tags/'+tag))
    if release['draft'] or not release['prerelease']:raise ValueError('Pilot must be a published prerelease')
    assets={a['name']:a for a in release['assets']}
    base='https://github.com/'+REPO+'/releases/download/'+tag+'/'
    def fetch(name):
        url=assets[name]['browser_download_url']
        if url!=base+name:raise ValueError('Unexpected asset origin')
        return get(url)
    checks={line.split('  ',1)[1]:line.split('  ',1)[0] for line in fetch('SHA256SUMS.txt').decode().splitlines()}
    data={}
    for name,digest in checks.items():
        if pathlib.PurePosixPath(name).name!=name:raise ValueError('Invalid asset filename')
        body=fetch(name)
        if hashlib.sha256(body).hexdigest()!=digest:raise ValueError('Corrupt pilot asset '+name)
        if name.endswith('.json'):data[name]=json.loads(body)
    meta=data['release-metadata.json'];feed=data['releases.friends-win-x64.json']
    if not meta['development'] or tag!='v'+meta['version']+'-pilot':raise ValueError('Unexpected pilot version')
    if meta['installer_sha256']!=checks[meta['installer']]:raise ValueError('Installer checksum mismatch')
    if len(feed['Assets'])!=1:raise ValueError('Expected one full package')
    entry=feed['Assets'][0]
    if entry['Version']!=meta['version'] or entry['PackageId']!='JengChat.Friends' or entry['Type']!='Full':raise ValueError('Invalid pilot feed')
    if entry['SHA256'].lower()!=checks[entry['FileName']]:raise ValueError('Feed checksum mismatch')
    return meta,assets,base
def main():
    p=argparse.ArgumentParser();p.add_argument('--baseline',required=True);p.add_argument('--target',required=True);p.add_argument('--output',default='_site');args=p.parse_args()
    baseline,assets,_=verified(args.baseline);target,_,target_url=verified(args.target)
    number=lambda v:tuple(int(x) for x in re.findall(r'\d+',v))
    if number(target['version'])<=number(baseline['version']):raise ValueError('Pilot target must be newer')
    if baseline['feed']!='https://mattarm555.github.io/JengChat-downloads/pilot/':raise ValueError('Baseline must use isolated pilot feed')
    if target['feed']!='https://mattarm555.github.io/JengChat-downloads/updates/':raise ValueError('Target must migrate to normal future feed')
    output=pathlib.Path(args.output);shutil.copytree('site',output,dirs_exist_ok=True)
    (output/'pilot').mkdir(exist_ok=True)
    (output/'pilot/source.txt').write_text(target_url+'\n',encoding='utf-8')
    info={'version':baseline['version'],'installer':assets[baseline['installer']]['browser_download_url'],'sha256':baseline['installer_sha256'],
          'release_url':'https://github.com/'+REPO+'/releases/tag/'+args.baseline,
          'notes':'INSTALL / UPDATE PILOT - ONE FRIEND FIRST\n\nInstall this beta 1 build, choose Update when beta 2 is offered, then choose Restart & Update. Confirm beta 2 is shown, your appearance/audio settings remain, and login, chat, multiplayer, Arena, Roulette and offline chess work. Report the result to the person who shared this link.\n\nBeta 2 switches to the normal friends feed for future releases. Broader distribution waits for this pilot result. These are unsigned testing builds.'}
    (output/'release.json').write_text(json.dumps(info,indent=2)+'\n',encoding='utf-8')
    # Deliberately omit updates/source.txt: production promotion is still gated.
    print('Verified both pilot releases; normal friends feed remains untouched')
if __name__=='__main__':main()
