"""Fake-codesigning profiles for an unsigned Bullgram IPA.

The repository ships fake provisioning profiles for ph.telegra.Telegraph. Rewrite
every bundle identifier inside them to our bundle id, push the expiry date
forward, and re-sign them with the fake identity imported into temp.keychain by
ImportCertificates.py. The IPA is re-signed by the user (ESign / Sideloadly),
so these only have to satisfy the build.
"""
import datetime, glob, os, plistlib, subprocess, sys, tempfile

OLD = "ph.telegra.Telegraph"


def rewrite(value, new):
    if isinstance(value, str):
        return value.replace(OLD, new)
    if isinstance(value, list):
        return [rewrite(v, new) for v in value]
    if isinstance(value, dict):
        return {k: rewrite(v, new) for k, v in value.items()}
    return value


def main(new_bundle):
    keychain = "temp.keychain"
    identity = "Apple Distribution: Telegram FZ-LLC (C67CF9S4VU)"
    for path in sorted(glob.glob("build-system/fake-codesigning/profiles/*.mobileprovision")):
        dec = subprocess.run(["security", "cms", "-D", "-i", path], check=True, stdout=subprocess.PIPE)
        data = plistlib.loads(dec.stdout)
        data = rewrite(data, new_bundle)
        data["ExpirationDate"] = datetime.datetime(2035, 1, 1)
        data.pop("DER-Encoded-Profile", None)
        with tempfile.NamedTemporaryFile(suffix=".plist", delete=False) as tf:
            plistlib.dump(data, tf)
            tmp = tf.name
        try:
            subprocess.run(["security", "cms", "-S", "-k", keychain, "-N", identity, "-i", tmp, "-o", path], check=True)
        finally:
            os.unlink(tmp)
        ver = plistlib.loads(subprocess.run(["security", "cms", "-D", "-i", path], check=True, stdout=subprocess.PIPE).stdout)
        print(path, ver["Entitlements"].get("application-identifier"), ver["ExpirationDate"])


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "com.usa8.messenger")
