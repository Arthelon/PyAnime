import os, re

import requests, threading
import bs4

from clint.textui import prompt, puts, validators

BASE_URL = 'http://www.shanaproject.com'
size_dict = {
    'MB': 1,
    'GiB': 2,
    'GB': 2
}


class RangeValidator:
    message = 'Please enter valid range'

    def __init__(self, msg=None):
        self.message = msg or RangeValidator.message

    def __call__(self, value):
        if value == '*' or re.fullmatch(r'\d+', value):
            return value
        else:
            reg = re.fullmatch(r'^(\d+)-(\d+)$', value)
            if reg:
                return int(reg[1]), int(reg[2])
            else:
                raise validators.ValidationError(self.message)


def main():
    command = prompt.options('Select a command', options=commands)
    while command != 'q':
        command()
        clear()
        command = prompt.options('Select a command', options=commands)
    pass


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


def request_data(url, params=None):
    try:
        req = requests.get(url, params=params)
        req.raise_for_status()
    except requests.HTTPError as error:
        SystemExit('Error occured\n'+error)
    return req


def parse_range(list):
    for range, size, links in list:
        if range.isdigit():
            yield int(range)
        elif range.startswith('Vol'):
            yield int(range.split(' ')[1])
        else:
            reg = re.fullmatch(r'(\d+).+?(\d+)', range)
            if reg:
                yield reg.group(1) + ' ' + reg.group(2)
            else:
                puts('Detected invalid range')
                yield None


def filter_queue(queue, low=True):
    pass


def bulk_download():
    search_term = prompt.query('Enter series title')
    # subber = prompt.query('Enter subber name (Optional)', validators=[])
    data = request_data(BASE_URL+'/search/', params={
        'title': search_term
        # 'subber': subber
    })

    soup = bs4.BeautifulSoup(data.content, 'lxml')
    if soup.select('center'):
        puts('No releases found')
    else:
        title_entries = soup.select('.release_block .release_title .release_text_contents a')
        filtered_entries = []
        for entry in title_entries:
            title = entry.getText()
            if not entry.get('rel') and title not in [entry[0] for entry in filtered_entries]:
                filtered_entries.append((title, entry.get('href')))
        selected = prompt.options('Select anime series', options=[entry[0] for entry in filtered_entries])
        wanted_range = prompt.query('Enter episode range (* for all)', validators=[RangeValidator()])

        data = request_data(BASE_URL+filtered_entries[int(selected)-1][1])
        soup = bs4.BeautifulSoup(data.content, 'lxml')
        episode_ranges = [tag.getText() for tag in soup.select('.release_block .release_episode')[1:]]
        file_sizes = [tag.getText() for tag in soup.select('.release_block .release_size')[1:]]
        download_links = [tag.get('href') for tag in soup.find_all('a', attrs={'type':'application/x-bittorrent'})]
        assert len(file_sizes) == len(download_links) == len(episode_ranges)

        episodes = list(zip(episode_ranges, file_sizes, download_links))
        download_queue = []
        if isinstance(wanted_range, tuple):
            for i, range in enumerate(parse_range(episodes)):
                if (isinstance(range, str) and range.split(' ')[0] >= wanted_range[0]\
                        and range.split(' ')[1] <= wanted_range[1]) or\
                            (wanted_range[0] <= range <= wanted_range[1]):
                                download_queue.append(episodes[i])
        elif wanted_range == '*':
            download_queue = episodes[:]
        elif wanted_range.isdigit():
            for i, range in enumerate(parse_range(episodes)):
                if isinstance(range, int) and range == int(wanted_range):
                    download_queue.append(episodes[i])
                else:
                    continue
        else:
            raise SystemExit('Invalid range')
        print(download_queue)
        input()
        filter_queue(download_queue)


commands = [
    {'selector': '1', 'prompt': 'Bulk download an anime series', 'return': bulk_download},
    {'selector': '2', 'prompt': 'Quit', 'return': 'q'}
]

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        puts('\nGoodbye!')
