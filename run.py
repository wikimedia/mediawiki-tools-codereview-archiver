#!/usr/bin/env python3
"""
Create HTML dumps for Extension:CodeReview
Copyright (C) 2019-2020 Kunal Mehta <legoktm@member.fsf.org>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import hashlib
import os
import re
import requests
import shutil


requests.utils.default_user_agent = \
    lambda name='': 'codereview-archiver/0.1 (legoktm)'
TEMPLATE = """<DOCTYPE html>
<html lang="en" dir="ltr">
<head>
<meta charset="utf-8">
<title>{title}</title>
<link rel="stylesheet" href="../ext.codereview.styles.css">
</head>
<body>
<h1>{title}</h1>
{body}
</body>
</html>
"""
RE_CONTENT = re.compile('<div id="mw-content-text" class="mw-body-content">(.*?)<noscript>',
                        flags=re.DOTALL | re.MULTILINE)


class Archiver:
    def __init__(self, repo: str):
        self.repo = repo
        self.session = requests.session()
        self.re1 = re.compile(
            r'href="https://www.mediawiki.org/wiki/'
            r'Special:Code/{}/(\d*?)"'.format(repo))
        self.re2 = re.compile(
            r'href="https://www.mediawiki.org/wiki/'
            r'Special:Code/{}/(\d*?)#c(\d.*?)"'.format(repo))
        self.re3 = re.compile(
            r'href="https://www.mediawiki.org/w/index.php\?title='
            r'Special:Code/{}/(\d*?)&amp;path="'.format(repo))
        self.re4 = re.compile(
            r'<h2>Diff <small>\[<a href="[^>]+>purge</a>\]</small></h2>')

    def rewrite_urls(self, text: str) -> str:
        text = self.re1.sub(r'href="./\g<1>.html"', text)
        text = self.re2.sub(r'href="./\g<1>.html#c\g<2>"', text)
        text = self.re3.sub(r'href="./\g<1>.html"', text)
        text = self.re4.sub(r'<h2>Diff</h2>', text)
        return text

    def download_url(self, rev: int) -> str:
        url = 'https://www.mediawiki.org/wiki/Special:Code/{}/{}'.format(
            self.repo, rev)
        hex = hashlib.md5(url.encode()).hexdigest()
        cache = '../cache/{}.html'.format(hex)
        if os.path.exists(cache):
            with open(cache) as f:
                return f.read()
        print('Fetching {}...'.format(url))
        r = self.session.get(url)
        r.raise_for_status()
        with open(cache, 'w') as f:
            f.write(r.text)
        return r.text

    def archive_revision(self, rev: int, text: str):
        if rev % 100 == 0:
            print('Archiving {} r{}'.format(self.repo, rev))
        fname = '../out/{}/{}.html'.format(self.repo, rev)
        found = RE_CONTENT.search(text)
        body = '<div id="mw-content-text" class="mw-body-content">{}</div>'.format(found.group(1))
        body = body.replace('href="/', 'href="https://www.mediawiki.org/')
        body = self.rewrite_urls(body)
        content = TEMPLATE.format(
            title='r{} {} - Code Review archive'.format(rev, self.repo),
            body=body
        )
        os.makedirs(os.path.dirname(fname), exist_ok=True)
        with open(fname, 'w') as f:
            f.write(content)

    def run(self, highest: int):
        for rev in range(1, highest+1):
            text = self.download_url(rev)
            self.archive_revision(rev, text)


def main():
    shutil.copy(
        os.path.join(os.path.dirname(__file__), 'ext.codereview.styles.css'),
        '../out/ext.codereview.styles.css'
    )
    mw = Archiver('MediaWiki')
    mw.run(115794)
    pwb = Archiver('pywikipedia')
    pwb.run(11781)


if __name__ == '__main__':
    main()
