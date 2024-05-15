# -*- coding: utf-8 -*-
import os.path
import pprint

from bs4 import BeautifulSoup
import requests
import threading
from os import path, remove
import asyncio
import aiohttp


class SdamGIA:
    def __init__(self, exam='ege'):
        '''

        :param exam: Выбор экзамена, каталог заданий которого будет использован
            Если передано oge, использует каталог заданий ОГЭ, в противном случае - каталог заданий ЕГЭ
        :type exam: str
        '''
        if exam.strip().lower() != 'oge':
            exam = 'ege'
        self.exam = exam
        self._BASE_DOMAIN = 'sdamgia.ru'
        self._SUBJECT_BASE_URL = {
            'math': f'https://math-{exam}.{self._BASE_DOMAIN}', 'mathb': f'https://mathb-ege.{self._BASE_DOMAIN}',
            'phys': f'https://phys-{exam}.{self._BASE_DOMAIN}',
            'inf': f'https://inf-{exam}.{self._BASE_DOMAIN}',
            'rus': f'https://rus-{exam}.{self._BASE_DOMAIN}',
            'bio': f'https://bio-{exam}.{self._BASE_DOMAIN}',
            'en': f'https://en-{exam}.{self._BASE_DOMAIN}',
            'chem': f'https://chem-{exam}.{self._BASE_DOMAIN}',
            'geo': f'https://geo-{exam}.{self._BASE_DOMAIN}',
            'soc': f'https://soc-{exam}.{self._BASE_DOMAIN}',
            'de': f'https://de-{exam}.{self._BASE_DOMAIN}',
            'fr': f'https://fr-{exam}.{self._BASE_DOMAIN}',
            'lit': f'https://lit-{exam}.{self._BASE_DOMAIN}',
            'sp': f'https://sp-{exam}.{self._BASE_DOMAIN}',
            'hist': f'https://hist-{exam}.{self._BASE_DOMAIN}',
        }
        self.tesseract_src = 'tesseract'
        self.html2img_chrome_path = 'chrome'
        self.grabzit_auth = {'AppKey': 'grabzit', 'AppSecret': 'grabzit'}

    async def __get(self, url: str, session: aiohttp.ClientSession):
        response = await session.get(url)
        text = await response.read()
        return text

    async def __async_requests(self, urls: list[str]):
        session = aiohttp.ClientSession()
        tasks = [asyncio.create_task(self.__get(req, session)) for req in urls]
        results = []
        for task in asyncio.as_completed(tasks):
            res = await task
            results.append(res)
        await session.close()
        return results

    def __parallel_requests(self, urls: list[str]):
        return asyncio.run(self.__async_requests(urls))

    def get_problem_by_id(self,
                          subject, ids: list[str]):
        """
        Получение информации о задаче по ее идентификатору

        :param subject: Наименование предмета
        :type subject: str

        :param ids: Идентификатор задачи
        :type ids: str
        """

        problems = []
        responses = self.__parallel_requests(
            [f'{self._SUBJECT_BASE_URL[subject]}/problem?id={i}' for i in ids])
        for resp in responses:
            doujin_page = resp
            soup = BeautifulSoup(doujin_page, 'html.parser')

            probBlock = soup.find('div', {'class': 'prob_maindiv'})
            if probBlock is None:
                return None

            for i in probBlock.find_all('img'):
                if not 'sdamgia.ru' in i['src']:
                    i['src'] = self._SUBJECT_BASE_URL[subject] + i['src']

            TOPIC_ID = ' '.join(probBlock.find(
                'span', {'class': 'prob_nums'}).text.split()[1:][:-2])
            ID = probBlock.find('span', {'class': 'prob_nums'}).find('a').text

            URL = f'{self._SUBJECT_BASE_URL[subject]}/problem?id={ID}'

            CONDITION, SOLUTION, ANSWER, ANALOGS = {}, {}, '', []

            try:
                CONDITION = {'text': probBlock.find_all('div', {'class': 'pbody'})[0].text.replace('\xad', '').replace('\xa0', ''),
                             'images': [i['src'] for i in
                                        probBlock.find_all('div', {'class': 'pbody'})[0].find_all('img')]
                             }
            except IndexError:
                pass

            try:
                SOLUTION = {'text': probBlock.find_all('div', {'class': 'pbody'})[1].text.replace('\xad', '').replace('\xa0'),
                            'images': [i['src'] for i in
                                       probBlock.find_all('div', {'class': 'pbody'})[1].find_all('img')]
                            }
            except IndexError:
                pass
            except AttributeError:
                pass

            try:
                ANSWER = probBlock.find(
                    'div', {'class': 'answer'}).text.replace('Ответ: ', '')
            except IndexError:
                pass
            except AttributeError:
                pass

            try:
                ANALOGS = [i.text for i in probBlock.find(
                    'div', {'class': 'minor'}).find_all('a')]
                if 'Все' in ANALOGS:
                    ANALOGS.remove('Все')
            except IndexError:
                pass
            except AttributeError:
                pass

            ONLY_TEXT = True
            if (not probBlock.find('div', {'class': 'pbody'}).find('table') is None) or CONDITION['images']:
                ONLY_TEXT = False
            result = {'id': ID, 'topic': TOPIC_ID, 'condition': CONDITION, 'solution': SOLUTION, 'answer': ANSWER,
                      'analogs': ANALOGS, 'url': URL, 'only_text': ONLY_TEXT}
            problems.append(result)
        return problems

    def search(self, subject, request, page=1):
        """
        Поиск задач по запросу

        :param subject: Наименование предмета
        :type subject: str

        :param request: Запрос
        :type request: str

        :param page: Номер страницы поиска
        :type page: int
        """
        doujin_page = requests.get(
            f'{self._SUBJECT_BASE_URL[subject]}/search?search={request}&page={str(page)}')
        soup = BeautifulSoup(doujin_page.content, 'html.parser')
        return [i.text.split()[-1] for i in soup.find_all('span', {'class': 'prob_nums'})]

    def get_test_by_id(self, subject, testid):
        """
        Получение списка задач, включенных в тест

        :param subject: Наименование предмета
        :type subject: str

        :param testid: Идентификатор теста
        :type testid: str
        """
        doujin_page = requests.get(
            f'{self._SUBJECT_BASE_URL[subject]}/test?id={testid}')
        soup = BeautifulSoup(doujin_page.content, 'html.parser')
        return [i.text.split()[-1] for i in soup.find_all('span', {'class': 'prob_nums'})]

    def get_category_by_id(self, subject, categoryids: list[str]):
        """
        Получение списка задач, включенных в категорию

        :param subject: Наименование предмета
        :type subject: str

        :param categoryid: Идентификатор категории
        :type categoryid: str

        :param page: Номер страницы поиска. По умолчанию или если передано 0, возвращает все существующие страницы
        :type page: int
        """

        page_ids = []
        for cat in categoryids:
            for i in range(1, 11):
                page_ids.append((cat, i))
        url_template = '{0}/test?&filter=all&theme={1}&page={2}'
        responses = self.__parallel_requests(
            [url_template.format(self._SUBJECT_BASE_URL[subject], i[0], i[1]) for i in page_ids])
        problems = []
        for doujin_page in responses:
            soup = BeautifulSoup(doujin_page, 'html.parser')
            problems.extend([i.text.split()[-1] for i in soup.find_all('span', {'class': 'prob_nums'})])
        return problems

    def get_catalog(self, subject):
        """
        Получение каталога заданий для определенного предмета

        :param subject: Наименование предмета
        :type subject: str
        """

        doujin_page = requests.get(
            f'{self._SUBJECT_BASE_URL[subject]}/prob_catalog')
        soup = BeautifulSoup(doujin_page.content, 'html.parser')
        catalog = []
        CATALOG = []

        for i in soup.find_all('div', {'class': 'cat_category'}):
            try:
                i['data-id']
            except:
                catalog.append(i)

        for topic in catalog[1:]:
            TOPIC_NAME = topic.find(
                'b', {'class': 'cat_name'}).text.split('. ')[1]
            TOPIC_ID = topic.find(
                'b', {'class': 'cat_name'}).text.split('. ')[0]
            if TOPIC_ID[0] == ' ':
                TOPIC_ID = TOPIC_ID[2:]
            if TOPIC_ID.find('Задания ') == 0:
                TOPIC_ID = TOPIC_ID.replace('Задания ', '')

            CATALOG.append(
                dict(
                    topic_id=TOPIC_ID,
                    topic_name=TOPIC_NAME,
                    categories=[
                        dict(
                            category_id=i['data-id'],
                            category_name=i.find(
                                'a', {'class': 'cat_name'}).text
                        )
                        for i in
                        topic.find('div', {'class': 'cat_children'}).find_all('div', {'class': 'cat_category'})]
                )
            )

        return CATALOG

    def generate_test(self, subject, problems=None):
        """
        Генерирует тест по заданным параметрам

        :param subject: Наименование предмета
        :type subject: str

        :param problems: Список заданий
        По умолчанию генерируется тест, включающий по одной задаче из каждого задания предмета.
        Так же можно вручную указать одинаковое количество задач для каждого из заданий: {'full': <кол-во задач>}
        Указать определенные задания с определенным количеством задач для каждого: {<номер задания>: <кол-во задач>, ... }
        :type problems: dict
        """

        if problems is None:
            problems = {'full': 1}

        if 'full' in problems:
            dif = {f'prob{i}': problems['full'] for i in range(
                1, len(self.get_catalog(subject)) + 1)}
        else:
            dif = {f'prob{i}': problems[i] for i in problems}

        return requests.get(f'{self._SUBJECT_BASE_URL[subject]}/test?a=generate', dif,
                            allow_redirects=False).headers['location'].split('id=')[1].split('&nt')[0]

    def generate_pdf(self, subject, testid, solution='', nums='',
                     answers='', key='', crit='',
                     instruction='', col='', pdf=True):
        """
        Генерирует pdf версию теста

        :param subject: Наименование предмета
        :type subject: str

        :param testid: Идентифигатор теста
        :type testid: str

        :param solution: Пояснение
        :type solution: bool

        :param nums: № заданий
        :type nums: bool

        :param answers: Ответы
        :type answers: bool

        :param key: Ключ
        :type key: bool

        :param crit: Критерии
        :type crit: bool

        :param instruction: Инструкция
        :type instruction: bool

        :param col: Нижний колонтитул
        :type col: str

        :param pdf: Версия генерируемого pdf документа
        По умолчанию генерируется стандартная вертикальная версия
        h - горизонтальная версия
        z - версия с крупным шрифтом
        m - версия с большим полем
        :type pdf: str

        """

        def a(a):
            if a == False:
                return ''
            return a

        return self._SUBJECT_BASE_URL[subject] + requests.get(f'{self._SUBJECT_BASE_URL[subject]}/test?'
                                                              f'id={testid}&print=true&pdf={pdf}&sol={a(solution)}&num={a(nums)}&ans={a(answers)}'
                                                              f'&key={a(key)}&crit={a(crit)}&pre={a(instruction)}&dcol={a(col)}',
                                                              allow_redirects=False).headers['location']

    def search_by_img(self, subject, path):
        """
        Поиск задач по тексту на изображении

        :param subject:
        :param path: Путь до изображения
        :type path: str
        """

        from sdamgia import images

        result = []
        words_from_img = images.img_to_str(path, self.tesseract_src).split()

        def parse(i):
            try:
                request_phrase = ' '.join(
                    [words_from_img[x] for x in range(i, i + 10)])

                doujin_page = requests.get(
                    f'{self._SUBJECT_BASE_URL[subject]}/search?search={request_phrase}&page={str(1)}')
                soup = BeautifulSoup(doujin_page.content, 'html.parser')
                problem_ids = [i.text.split()[-1]
                               for i in soup.find_all('span', {'class': 'prob_nums'})]

                for id in problem_ids:
                    if id not in result:
                        result.append(id)
            except Exception as E:
                pass

        thread_pool = []

        for i in range(0, len(words_from_img)):
            thread = threading.Thread(target=parse, args=(i,))
            thread_pool.append(thread)
            thread.start()

        for thread in thread_pool:
            thread.join()

        return result


if __name__ == '__main__':
    sdamgia = SdamGIA(exam='oge')
    print(sdamgia.get_problem_by_id('math', ['404147']))