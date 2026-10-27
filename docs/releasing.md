# Release checklist

This is the process for a future published release. It does not mean a release
exists today. CI artifacts and the current source-launch preview remain previews.
The maintainer, [@benczb](https://github.com/benczb), decides when to publish.

1. Select the reviewed commit and a version. Record user-facing changes,
   known limitations, tested platforms and migration/recovery notes in CHANGELOG.md.
2. Run relevant script, profile, launcher, GUI and PowerShell checks. Rebuild
   installer ZIPs/checksums where needed. Verify lockfiles and third-party notices.
3. Rehearse on clean supported Windows, Apple Silicon Mac and Linux desktops.
   Include existing installations, interrupted setup, port conflicts, local and
   Docker terminal choices, WSL update/reboot paths and Tailscale sign-in.
   Test Intel Mac source builds separately and report their actual outcome.
4. Verify authenticated Desktop use and remote access from another authorized
   tailnet device. Record checks that could not be performed. Do not describe a
   successful package build as proof of installation or remote access.
5. Build platform artifacts from the reviewed commit. For attendee-ready binaries,
   arrange Windows publisher signing and macOS Developer ID signing/notarization.
   Ad-hoc signing and passing `codesign --verify` alone do not establish publisher trust.
6. Prepare a draft GitHub release with versioned assets, SHA-256 checksums, source
   revision, release notes and platform instructions. Clearly label a prerelease
   and any unsigned artifacts. Review asset names and download URLs before publishing.
7. If changing the launcher's source snapshot, update the revision/hash in both
   launchers, test expectations and command guide, then verify the real archive.
   Do not silently change a published version's assets. Publish a new version for fixes.
8. Publish only after review. Check anonymous public downloads and update README
   commands/links to the intended channel. Keep source-launch and prebuilt-release
   behavior clearly distinguished. Never place credentials in artifacts or notes.

Repository settings are separate from documentation: enable private vulnerability
reporting if desired, configure branch protection/rulesets and signing credentials
through GitHub's supported settings. Do not claim these controls are enabled just
because their policies are documented.
