from api import scrapper


class Xamanager:
    ANDROID_CURRENT_SOURCE = 'https://raw.githubusercontent.com/xamarin/xamarin-android/main/README.md'
    ANDROID_OLDER_SOURCE = ('https://raw.githubusercontent.com/xamarin/xamarin-android/main/Documentation/previous'
                            '-releases.md')

    IOS_AND_MAC_SOURCE = 'https://raw.githubusercontent.com/xamarin/xamarin-macios/main/DOWNLOADS.md'

    def __init__(self):
        self.versions = {}
        self.dumps = {}
        self.all_versions = []
        self.platforms = ['android', 'ios', 'macos']
        self._db = None

        self._setup_db()
        self._load_from_db()

        if not len(self.versions):
            self._get_android_versions()
            self._get_ios_and_mac_versions()
            self._update_all_db()

    def get_current_version(self, platform: str):
        if platform not in self.versions.keys():
            return {}

        return self.versions[platform][0]

    def get_version(self, platform: str, version: str):
        if platform not in self.versions.keys():
            return {}

        xamarin = self._db.versions.find_one({'platform': platform, 'version': version}, {"_id": 0})
        return xamarin

    def search_new_versions(self):
        result = self._search_new_android_versions()
        result = self._search_new_ios_and_mac_versions() or result

        return result

    def _update_all_db(self):
        versions = self._db.versions
        # Get all versions

        items = list(map(lambda version: version.to_json(), self.all_versions))

        result = versions.insert_many(items)

        print(result.inserted_ids)

    def _setup_db(self):
        import os
        import certifi
        from pymongo import MongoClient

        mongo_db = os.environ.get('mongo_db')
        client = MongoClient(mongo_db, tlsCAFile=certifi.where())
        self._client = client
        self._db = client.xamanager

    def _load_from_db(self):
        from pymongo import DESCENDING
        from json import dumps

        versions = self._db.versions

        self.versions['android'] = list(versions.find({"platform": "android"}, {"_id": 0}).sort("identifier", DESCENDING))
        self.versions['ios'] = list(versions.find({"platform": "ios"}, {"_id": 0}).sort("identifier", DESCENDING))
        self.versions['macos'] = list(versions.find({"platform": "macos"}, {"_id": 0}).sort("identifier", DESCENDING))

        self.dumps['android'] = dumps(self.versions['android'])
        self.dumps['ios'] = dumps(self.versions['ios'])
        self.dumps['macos'] = dumps(self.versions['macos'])

    def _get_android_versions(self):
        # Get the current version
        source = scrapper.get_document_from_url(Xamanager.ANDROID_CURRENT_SOURCE)
        versions = scrapper.scrape_links(source)

        # Get previous versions
        source = scrapper.get_document_from_url(Xamanager.ANDROID_OLDER_SOURCE)
        versions.extend(scrapper.scrape_links(source))

        # versions.sort(key=lambda xamarin: xamarin.identifier, reverse=True)

        self.versions['android'] = versions
        self.all_versions.extend(versions)

    def _get_ios_and_mac_versions(self):
        source = scrapper.get_document_from_url(Xamanager.IOS_AND_MAC_SOURCE)
        versions = scrapper.scrape_links(source)

        ios = list(filter(lambda xamarin: xamarin.platform == 'ios', versions))
        # ios.sort(key=lambda xamarin: xamarin.identifier, reverse=True)

        macs = list(filter(lambda xamarin: xamarin.platform == 'mac', versions))
        # macs.sort(key=lambda xamarin: xamarin.identifier, reverse=True)

        self.versions['ios'] = ios
        self.versions['mac'] = macs
        self.all_versions.extend(versions)

    def _search_new_android_versions(self):
        source = scrapper.get_document_from_url(Xamanager.ANDROID_CURRENT_SOURCE)
        version = scrapper.scrape_links(source, expand_url=False)[0]
        new_version = False

        self._process_new_version(version, use_short_url=True)

        return new_version

    def _search_new_ios_and_mac_versions(self):
        source = scrapper.get_document_from_url(Xamanager.IOS_AND_MAC_SOURCE)
        versions = scrapper.scrape_links(source, first_in_table=True)
        new_version = False

        for version in versions:
            self._process_new_version(version)

        return new_version

    def _process_new_version(self, version, use_short_url=False):
        from json import dumps

        if use_short_url:
            db_version = self._db.versions.find_one({'short_url': version.short_url})
        else:
            db_version = self._db.versions.find_one({'identifier': version.identifier, 'platform': version.platform})

        if not db_version:
            if use_short_url:
                version.expand_url()
            payload = version.to_json()
            result = self._db.versions.insert_one(payload)
            self.versions[version.platform].append(version.to_json())
            self.dumps[version.platform] = dumps(self.versions[version.platform])
            print(result)
