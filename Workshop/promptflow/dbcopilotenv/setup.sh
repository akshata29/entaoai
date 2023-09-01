set -eux;
arch="$(dpkg --print-architecture)";
case "$arch" in
'amd64')
downloadUrl='https://download.java.net/java/early_access/jdk21/34/GPL/openjdk-21-ea+34_linux-x64_bin.tar.gz';
downloadSha256='d16356385a726320077563c6180f2eabf72ded64b5695f24f3e7a2d3980b1f11';
;;
*) echo >&2 "error: unsupported architecture: '$arch'"; exit 1 ;;
esac;

savedAptMark="$(apt-mark showmanual)";

wget --progress=dot:giga -O openjdk.tgz "$downloadUrl";
echo "$downloadSha256 *openjdk.tgz" | sha256sum --strict --check -;

mkdir -p "$JAVA_HOME";
tar --extract \
--file openjdk.tgz \
--directory "$JAVA_HOME" \
--strip-components 1 \
--no-same-owner \
;
rm openjdk.tgz*;

apt-mark auto '.*' > /dev/null;
[ -z "$savedAptMark" ] || apt-mark manual $savedAptMark > /dev/null;
apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=true;

# update "cacerts" bundle to use Debian's CA certificates (and make sure it stays up-to-date with changes to Debian's store)
# see https://github.com/docker-library/openjdk/issues/327
#     http://rabexc.org/posts/certificates-not-working-java#comment-4099504075
#     https://salsa.debian.org/java-team/ca-certificates-java/blob/3e51a84e9104823319abeb31f880580e46f45a98/debian/jks-keystore.hook.in
#     https://git.alpinelinux.org/aports/tree/community/java-cacerts/APKBUILD?id=761af65f38b4570093461e6546dcf6b179d2b624#n29
mkdir -p /etc/ca-certificates/update.d;
ls -al /etc/ca-certificates;
{
echo '#!/usr/bin/env bash';
echo 'set -Eeuo pipefail';
echo 'trust extract --overwrite --format=java-cacerts --filter=ca-anchors --purpose=server-auth "$JAVA_HOME/lib/security/cacerts"';
} > /etc/ca-certificates/update.d/docker-openjdk;
chmod +x /etc/ca-certificates/update.d/docker-openjdk;
/etc/ca-certificates/update.d/docker-openjdk;
update-ca-certificates;

# https://github.com/docker-library/openjdk/issues/331#issuecomment-498834472
find "$JAVA_HOME/lib" -name '*.so' -exec dirname '{}' ';' | sort -u > /etc/ld.so.conf.d/docker-openjdk.conf;
ldconfig;

# https://github.com/docker-library/openjdk/issues/212#issuecomment-420979840
# https://openjdk.java.net/jeps/341
java -Xshare:dump;

# basic smoke test
fileEncoding="$(echo 'System.out.println(System.getProperty("file.encoding"))' | jshell -s -)"; [ "$fileEncoding" = 'UTF-8' ]; rm -rf ~/.java;
javac --version;
java --version