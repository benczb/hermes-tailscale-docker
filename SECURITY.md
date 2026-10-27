# Security policy

This community installer can change host software, local credentials, services
and Tailscale forwarding. It remains a preview and has not undergone a complete
independent security audit. Automated checks do not establish safe behavior on
every machine or remote-device connectivity.

## Supported versions

Security fixes are developed on `main`. There are currently no published GitHub
releases or supported older release branches. Historical commits, expired CI
artifacts and older installer ZIPs do not receive separate security backports.
Command launchers intentionally pin a source snapshot; updating `main` does not
automatically update a downloaded launcher or the snapshot it uses. Snapshot and
package updates must be published explicitly. Consult current README and launcher
revision details before installing.

## Report a vulnerability privately

Do not open a public issue with exploit details, credentials or private logs.

1. Check this repository's [Security page](https://github.com/benczb/hermes-tailscale-docker/security).
   If **Report a vulnerability** is available, use GitHub's private reporting form.
   Private reporting is a repository setting; this policy does not enable it.
2. Otherwise use a private contact method published on the maintainer's
   [GitHub profile](https://github.com/benczb). If none is available, open an issue
   titled **Request for private security reporting channel**, without vulnerability
   details, and wait for a private channel before sending your report.

Provide the affected revision/platform, a minimal reproduction using dummy data,
expected and actual behavior, likely impact and any proposed fix. Redact secrets,
tailnet details and personal data. The maintainer coordinates investigation and
disclosure; no response-time commitment or bug bounty is offered.

An installer integration bug belongs here. A vulnerability confined to upstream
Hermes, Docker, Tailscale, Electron or another dependency should also follow that
project's own security reporting policy. Do not publish upstream exploit details
in this repository's public issues.

## Local precautions

- Review commands before running them; a checksum is not a publisher signature.
- Keep dashboard credentials, provider keys and OAuth JSON files out of issues,
  screenshots, chat and commits. Local installer credential files are not encrypted vaults.
- If a credential has been disclosed, revoke or rotate it with the issuing service.
  Removing it from the latest commit does not remove it from history or copies.
- Verify authentication and access from an authorized tailnet peer after setup.
  Do not publish the dashboard through Funnel or weaken its authentication.
