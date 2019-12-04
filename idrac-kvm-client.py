#!/usr/bin/python3

# iDRAC java KVM client script

import argparse
import getpass
import os
import platform
import ssl
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
import time

java_security = '''
jdk.tls.disabledAlgorithms=SSLv3, RC4, DES, MD5withRSA, DH keySize < 1024, EC keySize < 224, anon, NULL
'''

parser = argparse.ArgumentParser()
parser.add_argument("-s", "--server", type=str, required=True,
        help="iDRAC server hostname")
parser.add_argument("-u", "--user", type=str, required=True,
        help="iDRAC user")
parser.add_argument("-p", "--password", type=str,
        help="iDRAC password password")
parser.add_argument("--port", type=int, default=5900,
        help="iDRAC port number")
parser.add_argument("--nossl", action="store_true", default=False,
        help="don't use SSL/TLS when fetching KVM application")
parser.add_argument("--ssl-ignore-certificate", action="store_true",
        help="ignore SSL/TLS certificate on KVM application fetching connection")
parser.add_argument("--kbdmouse", action="store_true", default=False,
        help="use extra mouse and keyboard drivers")

args = parser.parse_args()

def fetch_file(url, outdir):
    udata = urllib.parse.urlparse(url)
    fname = os.path.basename(udata.path)
    print("%s: Fetching %s ..." % (sys.argv[0], url))
    fout = os.path.join(outdir, fname)
    local_filename, headers = urllib.request.urlretrieve(url=url, filename=fout)
    return local_filename

args.ssl = not args.nossl
del args.nossl
if not args.password:
    args.password = getpass.getpass("iDRAC password: ")

if args.ssl_ignore_certificate:
    # ugly
    ssl._create_default_https_context = ssl._create_unverified_context

url = "%s%s" % ("https://" if args.ssl else "http://", args.server)

tdir = tempfile.TemporaryDirectory(suffix=None, prefix=None, dir=None)

jar_file = "avctKVM.jar"
fetch_file(url="%s/software/%s" % (url, jar_file), outdir=tdir.name)

if args.kbdmouse:
    def unpack_drivers(fname):
        with zipfile.ZipFile(fname, 'r') as zo:
            inzip_files = zo.namelist()
            for zip_fname in inzip_files:
                if zip_fname.endswith(".so"):
                    print("%s: Extracting additional mouse and keyboard drivers: " % sys.argv[0], end="")
                    extracted = zo.extract(zip_fname, path=tdir.name)
                    print("%s " % os.path.basename(extracted), end="")
            print("")

    files = []
    if platform.system() == "Linux":
        if platform.machine() == "x86_64":
            files = ["avctVMLinux64.jar", "avctKVMIOLinux64.jar", "avctVMAPI_DLLLinux64.jar"]
        else:
            files = ["avctVMLinux32.jar", "avctKVMIOLinux32.jar", "avctVMAPI_DLLLinux32.jar"]

    elif platform.system == "MacOS":
        files = ["avctKVMIOMac64.jar", "avctVMMac64.jar", "avctVMAPI_DLLMac64.jar"]

    if not files:
        print("%s: --kbdmouse option is unsupported on this platform (%s, %s)" % (sys.argv[0], platform.system(), platform.machine()), file=sys.stderr)
        sys.exit(1)

    for f in files:
        try:
            local_file_name = fetch_file(url="%s/software/%s" % (url, f), outdir=tdir.name)
            unpack_drivers(local_file_name)
        except urllib.error.HTTPError as e:
            print("%s: Fetching %s failed: %s, skipping" % (sys.argv[0], url, e), file=sys.stderr)
            if e.code != 404:
                sys.exit(1)

java_security_file = os.path.join(tdir.name, "java.security")
with open(java_security_file, 'w') as f:
    f.write(java_security)

cmd = ["/usr/bin/java", "-cp", os.path.join(tdir.name, jar_file),
        "-Djava.security.properties=%s" % java_security_file,
        "-Djava.library.path=%s" % tdir.name,
        "com.avocent.idrac.kvm.Main",
        "ip=%s" % args.server,
        "kmport=%s" % args.port, "vport=%s" % args.port,
        "user=%s" % args.user,
        "passwd=%s" % args.password,
        "apcp=1", "reconnect=1", "vm=1", "version=2", "vmprivilege=true",
        "helpurl=%s/help/contents.html" % url ]

print("%s: Starting java KVM client (server=%s, user=%s, port=%d) ..." % (sys.argv[0], url, args.user, args.port))
subprocess.run(cmd, stdout=sys.stdout, stderr=sys.stderr)
print("%s: Ended" % sys.argv[0])
