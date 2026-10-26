(async()=>{try{
const response=await fetch('release.json',{cache:'no-store'});if(!response.ok)throw Error('Release unavailable');
const info=await response.json();const download=new URL(info.installer);
if(download.origin!=='https://github.com'||!download.pathname.startsWith('/mattarm555/JengChat-downloads/releases/download/'))throw Error('Invalid installer link');
document.getElementById('version').textContent='Version '+info.version+' · Friends testing';
const button=document.getElementById('download');button.href=download.href;button.hidden=false;
document.getElementById('status').textContent='One installation. Updates ask for your approval.';
document.getElementById('notes').textContent=info.notes;document.getElementById('checksum').textContent=info.sha256;
const release=document.getElementById('release');const url=new URL(info.release_url);
if(url.origin==='https://github.com'&&url.pathname.startsWith('/mattarm555/JengChat-downloads/releases/')){release.href=url.href;release.hidden=false;}
}catch{document.getElementById('version').textContent='The download is temporarily unavailable.';document.getElementById('status').textContent='Please try this page again shortly. Your installed JengChat can still be used.';}})();
