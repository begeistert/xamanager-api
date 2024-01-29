class Version:
    def __init__(self, platform: str, version: str, url: str, short_url: str):
        self.platform = platform
        self.version = version

        if version:
            version_unpacked = version.split('.')
            major = int(version_unpacked[0])
            minor = int(version_unpacked[1])
            patch = int(version_unpacked[2])
            if len(version_unpacked) > 3:
                build = int(version_unpacked[3])
            else:
                build = 0

            self.identifier = major << 24 | minor << 16 | patch << 8 | build

        self.url = url
        self.short_url = short_url

    @staticmethod
    def from_json(json_version: dict) -> 'Version':
        return Version(json_version['platform'], json_version['version'], json_version['url'], json_version['short_url'])

    def to_json(self) -> dict:
        obj = {
            'platform': self.platform,
            'version': self.version,
            'identifier': self.identifier,
            'url': self.url,
            'short_url': self.short_url
        }

        return obj

    def to_payload(self) -> dict:
        return {"name": f'Xamarin.{self.platform}', 'version': self.version, 'uri': self.url}

    def expand_url(self):
        import requests

        session = requests.Session()
        resp = session.head(self.short_url, allow_redirects=True)
        if resp.status_code == 200:
            self.url = resp.url
            self.platform = self.url.split('/')[-1].split('-')[0].split('.')[-1]
            version = self.url.split('/')[-1].replace('.pkg', '').replace(f'xamarin.{self.platform}-', '')
            if '-' in version:
                version = version.replace('-', '.')
            if '?' in version:
                version = version.split('?')[0]
            if 'monotouch' in version:
                version = version.replace('monotouch.', '')
                self.platform = 'ios'

            self.version = version

            if version:
                version_unpacked = version.split('.')
                major = int(version_unpacked[0])
                minor = int(version_unpacked[1])
                patch = int(version_unpacked[2])
                if len(version_unpacked) > 3:
                    build = int(version_unpacked[3])
                else:
                    build = 0

                self.identifier = major << 24 | minor << 16 | patch << 8 | build

