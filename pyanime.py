import os, re

import requests, threading
import bs4

from clint.textui import prompt, puts, validators, columns

BASE_URL = 'http://www.shanaproject.com'
OUTPATH = os.path.join(os.getenv('HOME'), 'PyAnime/')
size_dict = {
    'KB': 0,
    'MB': 1,
    'GiB': 2,
    'GB': 2
}
MAX_THREADS = 5


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
        puts()
        command = prompt.options('Select a command', options=commands)
    pass


def change_download_location():
    to_path = prompt.query('Enter output path (~/PyAnime by default)', validators=[validators.PathValidator()])
    print('Path change to \'{:s}\''.format(to_path))


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


def request_data(url, params=None):
    try:
        req = requests.get(url, params=params)
        req.raise_for_status()
    except requests.HTTPError as error:
        SystemExit('Error occured\n'+error)
    return req


def download_ep(download_path):
    data = request_data(BASE_URL+download_path)
    # Implement download code


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


def compare_file_sizes(new, master):
    reg_new = re.fullmatch(r'([\d\.]+)(\w+)', new)
    reg_master = re.fullmatch(r'([\d\.]+)(\w+)', master)
    if reg_new and reg_master:
        if size_dict[reg_new.group(2)] < size_dict[reg_master.group(2)]\
                or float(reg_new.group(1)) < float(reg_master.group(1)):
            return True
        return False
    else:
        raise SystemExit('Invalid file sizes:', new, master)


def filter_queue(queue, low=True):
    values_dict = dict()
    print(queue)
    for i, item in enumerate(queue):
        if item[0] == '\xa0':
            continue
        if item[0] not in values_dict\
                or compare_file_sizes(item[1], values_dict[item[0]][1]):
            values_dict[item[0]] = (i, item[1],)
    return [queue[int(index)] for index in [i[0] for i in values_dict.values()]]



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
        download_queue = filter_queue(download_queue)
        if download_queue:
            puts(columns(['Episode', 10], ['Size', 10]))
            for episode in download_queue:
                puts(columns([episode[0], 10], [episode[1], 10]))
        else:
            puts('No entries to download')
            return
        input('Proceed with download? (Ctrl-C to exit)')
        current_downloads = []
        for item in download_queue:
            t = threading.Thread(target=request_data, args=BASE_URL+'item')
            if current_downloads >= MAX_THREADS:
                current_downloads[0].join()
            t.start()
        for thread in current_downloads:
            thread.join()
        puts('Download completed')



commands = [
    {'selector': '1', 'prompt': 'Bulk download an anime series', 'return': bulk_download},
    {'selector': '2', 'prompt': 'Change download location', 'return': change_download_location},
    {'selector': '3', 'prompt': 'Quit', 'return': 'q'}
]

if __name__ == '__main__':
    if not os.path.isdir(OUTPATH):
        os.mkdir(OUTPATH)
    try:
        main()
    except KeyboardInterrupt:
        puts('\nGoodbye!')
