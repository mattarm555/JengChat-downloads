# Beta 5 publication acceptance

On November 5, 2026, the owner explicitly approved a one-time waiver of the
second-machine installer/update test for beta 5 and the workflow exception
needed to publish it. Record this release's second-machine installation/update
and settings checks as waived, not as passing tests. Future versions retain
the normal pilot requirement; the exception only accepts v2.1.0-beta.5.

The owner confirmed live login and chat with the new server IP and certificate.
Clean Windows CI passed for source commit
4faa34da0ef4538d196c3c43a51b81779645a833 in run
https://github.com/mattarm555/JengChat/actions/runs/42075008164.
The installer, packaged lobby flows, TLS recovery, native updater download and
failure cases, release checksums and page/feed generation were verified.

Public files contain the compiled installer, update package, portable build and
metadata. The private JengChat source archive is excluded, with SHA256SUMS
covering the published files. Required third-party license/source material
remains bundled. Application source is retained in its private repository,
identified by the recorded commit and tag v2.1.0-beta.5.
