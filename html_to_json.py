import re
import json
from bs4 import BeautifulSoup
from utils import clean_up, get_html, tokenize


def html_to_json(url):
    category, uid = tokenize(url)
    schema_name = 'schema/{}.json'.format(category)
    with open(schema_name, 'rb') as fp:
        template = json.load(fp)

    html_doc = get_html(url)
    soup = BeautifulSoup(html_doc, 'html.parser')

    table_title = None
    result = {}
    ignore_image = True
    for tr in soup.find_all('tr'):
        # keep only the most bottom level tr
        if tr.find_all('tr'):
            continue
        is_title_row = False
        row_content = []
        for td in tr.find_all('td'):
            if ignore_image and td.find_all('img'):
                continue
            text = clean_up(td.text)
            if text in template:
                table_title = text
                is_title_row = True
                row_titles = template[table_title]
                ignore_image = row_titles['ignore image']
                result[table_title] = {}
                break
            link = ''
            for a in td.find_all('a'):
                link = a.get('href')
            row_content.append({'text': text, 'link': link})

        if is_title_row:
            continue

        if not row_content or not table_title:
            continue

        column_index = row_titles['column index']
        strict_match = row_titles['strict match']
        regex_match = row_titles['regex match']
        terminate_on_mismatch = row_titles['terminate on mismatch']

        matched = False
        if len(row_content) > column_index + 1:
            candidate_row_title = row_content[column_index]['text']
            for s in strict_match:
                if s == candidate_row_title and s not in result[table_title]:
                    matched = True
                    result[table_title][s] = row_content[column_index + 1:]
                    break
            if not matched:
                for s in regex_match:
                    if re.match(s, candidate_row_title):
                        matched = True
                        category, race_id = tokenize(row_content[column_index + 1]['link'])
                        result[table_title][race_id] = row_content[column_index:]
                        break
        if terminate_on_mismatch and not matched:
            table_title = None
            ignore_image = True
    return result


if __name__ == '__main__':
    urls = ['http://www.ourcampaigns.com/RaceDetail.html?RaceID=613722',
            'http://www.ourcampaigns.com/CandidateDetail.html?CandidateID=234785',
            'http://www.ourcampaigns.com/ContainerDetail.html?ContainerID=131',
            'http://www.ourcampaigns.com/RaceDetail.html?RaceID=548556',
            'http://www.ourcampaigns.com/RaceDetail.html?RaceID=370463',
            'http://www.ourcampaigns.com/RaceDetail.html?RaceID=486821']

    for i, url in enumerate(urls):
        result = html_to_json(url)
        saveas = 'converted_{}.json'.format(i)
        with open(saveas, 'wb') as fp:
            json.dump(result, fp)
